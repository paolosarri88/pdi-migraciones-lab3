"""Recepción asistida, atención exclusiva por funcionario e historial editable."""
import base64
import json
import os
import re
import secrets
import time
from pathlib import Path
from flask import request,jsonify,g,session,send_file
from demo_characters import CHARACTERS


def install(ctx):
    app,auth,one,rows,db,fail,event,now=(ctx[k] for k in ('app','auth','one','rows','db','fail','event','now'))
    c=ctx['connect'](ctx['DATA'],initialize=True)
    columns={'users':{'alias':'TEXT','birth_info':'TEXT','birthplace':'TEXT'},'appointments':{'serving_by':'INTEGER','desk':'TEXT'},'events':{'deleted_at':'TEXT'},'institutional':{'criminal_status':'TEXT','criminal_notes':'TEXT'}}
    for table,additions in columns.items():
        present={r[0] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=?",(table,)).fetchall()} if os.environ.get('DB_HOST') else {r[1] for r in c.execute('PRAGMA table_info('+table+')').fetchall()}
        for name,typ in additions.items():
            if name not in present:c.execute('ALTER TABLE '+table+' ADD COLUMN '+name+' '+typ)
    c.executescript('''CREATE TABLE IF NOT EXISTS portal_migrations(id INTEGER PRIMARY KEY,name TEXT UNIQUE);
    CREATE TABLE IF NOT EXISTS event_edits(id INTEGER PRIMARY KEY,event_id INTEGER,old_status TEXT,old_note TEXT,action TEXT,reason TEXT,actor_id INTEGER,created TEXT);
    CREATE TABLE IF NOT EXISTS reception_captures(id INTEGER PRIMARY KEY,visit_id INTEGER UNIQUE,user_id INTEGER,id_path TEXT,id_mime TEXT,id_name TEXT,face_path TEXT,created TEXT);''')
    if not c.execute('SELECT id FROM portal_migrations WHERE name=?',('gta-citizens-v1',)).fetchone():
        for uid,name,alias,nationality,birth,place,criminal,note in CHARACTERS:
            old=c.execute("SELECT name FROM users WHERE id=? AND role='citizen' AND email LIKE '%@demo.pdi.cl'",(uid,)).fetchone()
            if not old:continue
            c.execute('UPDATE users SET name=?,alias=?,nationality=?,birth_info=?,birthplace=? WHERE id=?',(name,alias,nationality,birth,place,uid))
            c.execute('UPDATE events SET actor_name=? WHERE actor_name=?',(name,old[0]))
            c.execute('UPDATE institutional SET criminal_status=?,criminal_notes=?,border=?,notes=? WHERE user_id=?',(criminal,note,['Aeropuerto de Santiago','Los Libertadores','Chacalluta'][uid%3],'Ingreso y antecedentes administrativos inventados para la PoC.',uid))
        c.execute('INSERT INTO portal_migrations(name) VALUES(?)',('gta-citizens-v1',))
    # Keep existing in-progress visits; legacy ones are explicitly claimed on demand.
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_attention_per_staff ON appointments(serving_by) WHERE status='En atención' AND serving_by IS NOT NULL")
    # Walk-ins do not reserve a future appointment slot.
    c.execute('DROP INDEX IF EXISTS appointment_slot')
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS appointment_slot ON appointments(date,time) WHERE status IN ('Confirmada','Pendiente de confirmación')")
    c.commit();c.close()

    @app.patch('/api/appointments/<int:aid>/attention')
    @auth(staff=True)
    def attention(aid):
        # Serialize assignment across tabs/workers before checking exclusive ownership.
        if os.environ.get('DB_HOST'):db().execute('SELECT id FROM users WHERE id=? FOR UPDATE',(g.user['id'],))
        else:db().execute('UPDATE users SET active=active WHERE id=?',(g.user['id'],))
        d=request.get_json(silent=True) or {};action=d.get('action')
        a=one('SELECT * FROM appointments WHERE id=?',(aid,))
        if not a:return fail('Atención no encontrada.',404)
        active=one("SELECT id FROM appointments WHERE serving_by=? AND status='En atención'",(g.user['id'],))
        desk='Módulo '+str(g.user['id'])
        if action in ('start','claim'):
            if active and active['id']!=aid:return fail('Finaliza tu atención actual antes de llamar a otra persona.',409)
            if action=='start' and a['status']!='Presente':return fail('Esta persona no está disponible en la fila.',409)
            if action=='claim' and (a['status']!='En atención' or a['serving_by']):return fail('Esta atención ya tiene responsable.',409)
            changed=db().execute("UPDATE appointments SET serving_by=?,desk=?,status='En atención' WHERE id=? AND status=? AND serving_by IS NULL",(g.user['id'],desk,aid,a['status']))
            # Re-read to handle a competing staff member calling the same turn.
            assigned=one('SELECT serving_by FROM appointments WHERE id=?',(aid,))
            if assigned['serving_by']!=g.user['id']:return fail('Otro funcionario ya tomó este turno.',409)
            db().execute('UPDATE visits SET started=COALESCE(started,?) WHERE appointment_id=?',(now(),aid))
        elif action=='finish':
            if a['status']!='En atención' or a['serving_by']!=g.user['id']:return fail('Solo el funcionario que atiende puede finalizar esta sesión.',409)
            db().execute("UPDATE appointments SET status='Finalizada' WHERE id=?",(aid,));db().execute('UPDATE visits SET finished=? WHERE appointment_id=?',(now(),aid))
        else:return fail('Acción no válida.')
        if a['request_id']:event(a['request_id'],'Atención iniciada' if action!='finish' else 'Atención finalizada',desk+' · '+g.user['name'])
        return jsonify(ok=True,user_id=a['user_id'],desk=desk)

    @app.get('/api/reception/board')
    def reception_board():
        items=rows("SELECT v.ticket,a.desk,u.name as owner_name FROM appointments a JOIN visits v ON v.appointment_id=a.id JOIN users u ON u.id=a.user_id WHERE a.status='En atención' AND a.serving_by IS NOT NULL ORDER BY v.started DESC")
        return jsonify(items=items)

    @app.post('/api/reception/identify')
    def identify():
        data=request.get_json(silent=True) or {};identifier=str(data.get('identifier','')).strip().upper()
        if re.fullmatch(r'\d{7,8}-[0-9K]',identifier):
            u=one("SELECT id FROM users WHERE demo_run=? AND role='citizen' AND active=1",(identifier.replace('-',''),))
            if not u:return fail('RUN no encontrado. Acércate al mesón de atención.',404)
            a=one("SELECT * FROM appointments WHERE user_id=? AND date=? AND status NOT IN ('Cancelada','Finalizada') ORDER BY id LIMIT 1",(u['id'],now()[:10]))
            if a and a['status']=='Pendiente de confirmación':return fail('Confirma tu cita en el portal o solicita ayuda en el mesón.',409)
            uid=u['id']
        elif re.fullmatch(r'CITA-[0-9A-F]{4,12}',identifier):
            a=one('SELECT * FROM appointments WHERE code=?',(identifier,))
            if not a or a['date']!=now()[:10] or a['status'] not in ('Confirmada','Presente','En atención'):return fail('El código no corresponde a una cita confirmada para hoy.',409)
            uid=a['user_id']
        else:return fail('Ingresa RUN sin puntos y con guion, o código CITA-XXXX.')
        if a and a['status'] in ('Presente','En atención'):
            v=one('SELECT ticket FROM visits WHERE appointment_id=?',(a['id'],))
            return jsonify(registered=True,ticket=v['ticket'] if v else '',status=a['status'],desk=a['desk'])
        # Only one short-lived reception grant per kiosk browser session.
        token=secrets.token_urlsafe(32);session['reception']={'token':token,'uid':uid,'aid':a['id'] if a else None,'until':time.time()+900}
        return jsonify(token=token,registered=False)

    def image_payload(data,key,limit,pdf=False):
        try:raw=base64.b64decode(data.get(key,''),validate=True)
        except Exception:return None
        if not raw or len(raw)>limit:return None
        if raw.startswith(b'\x89PNG\r\n\x1a\n'):return raw,'image/png','.png'
        if raw.startswith(b'\xff\xd8\xff'):return raw,'image/jpeg','.jpg'
        if pdf and raw.startswith(b'%PDF-'):return raw,'application/pdf','.pdf'
        return None

    @app.post('/api/reception/complete')
    def complete():
        d=request.get_json(silent=True) or {};grant=session.get('reception') or {}
        if grant.get('until',0)<time.time() or not secrets.compare_digest(str(d.get('token','')),grant.get('token','!')):return fail('La recepción venció. Comienza nuevamente.',403)
        identification=image_payload(d,'identification',5*1024*1024,True);face=image_payload(d,'face',500*1024)
        if not identification or not face or face[1]!='image/jpeg':return fail('Adjunta la copia del documento (PDF/JPG/PNG, hasta 5 MB) y una captura de cámara (hasta 500 KB).')
        uid=grant['uid']
        if os.environ.get('DB_HOST'):db().execute('SELECT id FROM users WHERE id=? FOR UPDATE',(uid,))
        else:db().execute('UPDATE users SET active=active WHERE id=?',(uid,))
        if one("SELECT id FROM appointments WHERE user_id=? AND status IN ('Presente','En atención')",(uid,)):return fail('Tu llegada ya está registrada. Acércate al mesón si necesitas ayuda.',409)
        aid=grant['aid']
        if aid:
            a=one('SELECT * FROM appointments WHERE id=?',(aid,))
            if not a or a['status']!='Confirmada' or a['date']!=now()[:10]:return fail('La cita cambió. Comienza de nuevo o solicita ayuda.',409)
            db().execute("UPDATE appointments SET status='Presente' WHERE id=?",(aid,))
        else:
            aid=db().execute('INSERT INTO appointments(user_id,date,time,office,status,code,reason) VALUES(?,?,?,?,?,?,?)',(uid,now()[:10],now()[11:16],'Recepción presencial','Presente','CITA-'+secrets.token_hex(4).upper(),'Llegada sin cita desde tótem')).lastrowid
        ticket=f'A-{aid:03}';vid=db().execute('INSERT INTO visits(appointment_id,ticket,entered) VALUES(?,?,?)',(aid,ticket,now())).lastrowid
        id_path=secrets.token_hex(20)+identification[2];face_path=secrets.token_hex(20)+face[2]
        ctx['put_document'](ctx['DATA'],id_path,identification[0],identification[1]);ctx['put_document'](ctx['DATA'],face_path,face[0],face[1])
        db().execute('INSERT INTO reception_captures(visit_id,user_id,id_path,id_mime,id_name,face_path,created) VALUES(?,?,?,?,?,?,?)',(vid,uid,id_path,identification[1],Path(str(d.get('name','identificacion'))).name[:160],face_path,now()))
        session.pop('reception',None)
        return jsonify(ticket=ticket,status='Presente'),201

    @app.get('/api/people/<int:uid>/reception')
    @auth(staff=True)
    def reception(uid):
        captures=rows('SELECT c.id,c.id_mime,c.id_name,c.created,v.ticket,a.id as appointment_id,a.status,a.serving_by,a.desk FROM reception_captures c JOIN visits v ON v.id=c.visit_id JOIN appointments a ON a.id=v.appointment_id WHERE c.user_id=? ORDER BY c.id DESC LIMIT 1',(uid,))
        active=one("SELECT id,status,serving_by,desk FROM appointments WHERE user_id=? AND status IN ('Presente','En atención') ORDER BY id DESC LIMIT 1",(uid,))
        u=one("SELECT alias,birth_info,birthplace FROM users WHERE id=? AND role='citizen'",(uid,))
        return jsonify(capture=captures[0] if captures else None,attention=active,extra=u)

    @app.get('/api/reception/captures/<int:cid>/<kind>')
    @auth(staff=True)
    def captured_file(cid,kind):
        capture=one('SELECT * FROM reception_captures WHERE id=?',(cid,))
        if not capture or kind not in ('identification','face'):return fail('Archivo no encontrado.',404)
        return send_file(ctx['get_document'](ctx['DATA'],capture['id_path'] if kind=='identification' else capture['face_path']),mimetype=capture['id_mime'] if kind=='identification' else 'image/jpeg',download_name=capture['id_name'] if kind=='identification' else 'captura.jpg')

    @app.patch('/api/events/<int:eid>')
    @app.delete('/api/events/<int:eid>')
    @auth(staff=True)
    def edit_event(eid):
        original=one('SELECT * FROM events WHERE id=?',(eid,));data=request.get_json(silent=True) or {};reason=str(data.get('reason','')).strip()
        if not original or original['deleted_at']:return fail('Anotación no encontrada.',404)
        if not 10<=len(reason)<=2000:return fail('Indica el motivo del cambio (10 a 2.000 caracteres).')
        r=ctx['request_record'](original['request_id'])
        deleting=request.method=='DELETE';title=str(data.get('status',original['status'])).strip();note=str(data.get('note',original['note'])).strip();new_state=data.get('request_status')
        if not deleting and (not 3<=len(title)<=100 or not 1<=len(note)<=3000):return fail('Revisa el título y el texto de la anotación.')
        if new_state:
            if new_state not in ctx['STATUSES']:return fail('Estado no válido.')
            if r['status']=='Cerrada':return fail('Administración debe reabrir el expediente cerrado antes de corregir su estado.',409)
            if new_state=='Resuelta' and any(x['status']!='Aceptado' for x in ctx['document_groups'](r)):return fail('Acepta los documentos antes de resolver.',409)
            db().execute('UPDATE requests SET status=?,updated=? WHERE id=?',(new_state,now(),r['id']))
        db().execute('INSERT INTO event_edits(event_id,old_status,old_note,action,reason,actor_id,created) VALUES(?,?,?,?,?,?,?)',(eid,original['status'],original['note'],'delete' if deleting else 'edit',reason,g.user['id'],now()))
        if deleting:db().execute('UPDATE events SET deleted_at=? WHERE id=?',(now(),eid))
        else:db().execute('UPDATE events SET status=?,note=? WHERE id=?',(title,note,eid))
        ctx['notify'](r['user_id'],'Historial actualizado',r['folio']+': se corrigió una anotación del expediente.',f'/solicitudes/{r["id"]}')
        return jsonify(ok=True)

    @app.patch('/api/requests/<int:rid>/assignment')
    @auth(staff=True)
    def assignment(rid):
        r=ctx['request_record'](rid)
        if not r:return fail('Expediente no encontrado.',404)
        take=bool((request.get_json(silent=True) or {}).get('take',True))
        if r['assigned_to'] not in (None,g.user['id']) and g.user['role']!='admin':return fail('Este expediente ya tiene responsable. Administración puede reasignarlo.',409)
        db().execute('UPDATE requests SET assigned_to=? WHERE id=?',(g.user['id'] if take else None,rid))
        event(rid,'Responsable actualizado',('Revisión a cargo de '+g.user['name']) if take else 'Expediente liberado para revisión.','internal')
        return jsonify(ok=True)

    @app.get('/api/workload')
    @auth(staff=True)
    def workload():
        waiting=one("SELECT COUNT(*) as total FROM appointments WHERE status='Presente'")['total']
        online=one("SELECT COUNT(*) as total FROM requests r WHERE r.channel='online' AND r.status NOT IN ('Resuelta','Cerrada','Rechazada') AND (r.appointment_requested=1 OR r.status IN ('Recibida','En revisión') OR EXISTS(SELECT 1 FROM documents d WHERE d.request_id=r.id AND d.superseded=0 AND d.review_status='En revisión'))")['total']
        active=one("SELECT a.id,a.user_id,u.name as owner_name,a.desk FROM appointments a JOIN users u ON u.id=a.user_id WHERE a.status='En atención' AND a.serving_by=?",(g.user['id'],))
        return jsonify(waiting=waiting,online=online,active=active)

    @app.post('/api/requests/<int:rid>/reception-document')
    @auth(staff=True)
    def reception_document(rid):
        r=ctx['request_record'](rid);data=request.get_json(silent=True) or {}
        if not r or r['status'] in ('Resuelta','Cerrada','Rechazada'):return fail('Expediente no disponible.',409)
        capture=one('SELECT * FROM reception_captures WHERE id=? AND user_id=?',(data.get('capture_id'),r['user_id']))
        if not capture:return fail('Copia de recepción no disponible para esta persona.',404)
        requirement='Documento de identidad'
        if requirement not in [x['name'] for x in ctx['document_groups'](r)]:return fail('Este expediente no solicita documento de identidad.')
        current=one('SELECT review_status FROM documents WHERE request_id=? AND requirement=? AND superseded=0',(rid,requirement))
        if current and current['review_status']=='Aceptado':return fail('Este requisito ya está aceptado.',409)
        if one('SELECT COUNT(*) as total FROM documents WHERE request_id=?',(rid,))['total']>=12:return fail('El expediente admite hasta 12 documentos.')
        source=ctx['get_document'](ctx['DATA'],capture['id_path'])
        size=len(source.getvalue()) if hasattr(source,'getvalue') else source.stat().st_size
        db().execute('UPDATE documents SET superseded=1 WHERE request_id=? AND requirement=? AND superseded=0',(rid,requirement))
        did=db().execute('INSERT INTO documents(request_id,name,path,mime,size,created,requirement,origin,origin_note) VALUES(?,?,?,?,?,?,?,?,?)',(rid,capture['id_name'],capture['id_path'],capture['id_mime'],size,now(),requirement,'presencial','Copia del tótem capturada el '+capture['created']+'. Pendiente de revisión visual por el funcionario.')).lastrowid
        event(rid,'Identificación incorporada desde recepción','Se incorporó la copia presentada en el tótem. El funcionario debe registrar su decisión documental.')
        return jsonify(id=did),201
