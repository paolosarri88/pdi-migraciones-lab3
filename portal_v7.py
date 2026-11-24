"""Agendamiento ciudadano, recepción provisional y acciones reversibles."""
import json
import os
import re
import secrets
import time
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from flask import request,jsonify,g,session,send_file

SLOTS=[f'{h:02}:{m:02}' for h in range(9,16) for m in (0,30)]
FINAL=('Resuelta','Cerrada','Rechazada')

def install(ctx):
    app,auth,db,one,rows,fail,now,event,notify=(ctx[k] for k in ('app','auth','db','one','rows','fail','now','event','notify'))
    c=ctx['connect'](ctx['DATA'],initialize=True)
    c.executescript('''CREATE TABLE IF NOT EXISTS action_history(id INTEGER PRIMARY KEY,event_id INTEGER,last_event_id INTEGER,request_id INTEGER,before_json TEXT,after_json TEXT,undone INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS notification_deliveries(id INTEGER PRIMARY KEY,notification_id INTEGER,channel TEXT,status TEXT,created TEXT,UNIQUE(notification_id,channel));
    CREATE TABLE IF NOT EXISTS appointment_code_aliases(id INTEGER PRIMARY KEY,code TEXT UNIQUE,appointment_id INTEGER);
    ''')
    for table,name,typ in [('appointments','booking_source',"TEXT DEFAULT 'staff'"),('reception_captures','guest_name','TEXT')]:
        present={r[0] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=?",(table,)).fetchall()} if os.environ.get('DB_HOST') else {r[1] for r in c.execute('PRAGMA table_info('+table+')').fetchall()}
        if name not in present:c.execute('ALTER TABLE '+table+' ADD COLUMN '+name+' '+typ)
    if not c.execute('SELECT id FROM portal_migrations WHERE name=?',('numeric-bookings-v1',)).fetchone():
        for aid,code in c.execute('SELECT id,code FROM appointments').fetchall():
            if not re.fullmatch(r'CITA-\d+',code):
                c.execute('INSERT INTO appointment_code_aliases(code,appointment_id) VALUES(?,?)',(code,aid))
                value='CITA-'+str(700000+aid)
                while c.execute('SELECT id FROM appointments WHERE code=?',(value,)).fetchone():value='CITA-'+str(secrets.randbelow(900000)+100000)
                c.execute('UPDATE appointments SET code=? WHERE id=?',(value,aid))
        c.execute("UPDATE appointments SET status='Confirmada' WHERE status='Pendiente de confirmación'")
        c.execute('UPDATE requests SET appointment_requested=0')
        c.execute('INSERT INTO portal_migrations(name) VALUES(?)',('numeric-bookings-v1',))
    c.commit();c.close()

    def lock_case(rid):
        if os.environ.get('DB_HOST'):db().execute('SELECT id FROM requests WHERE id=? FOR UPDATE',(rid,))
        else:db().execute('UPDATE requests SET updated=updated WHERE id=?',(rid,))
    def snapshot(rid):
        r=one('SELECT * FROM requests WHERE id=?',(rid,))
        return {'request':r, 'documents':rows('SELECT * FROM documents WHERE request_id=? ORDER BY id',(rid,)), 'requirements':rows('SELECT * FROM extra_requirements WHERE request_id=? ORDER BY id',(rid,)), 'appointments':rows('SELECT * FROM appointments WHERE request_id=? ORDER BY id',(rid,)), 'notification_max':one('SELECT COALESCE(MAX(id),0) as n FROM notifications WHERE user_id=?',(r['user_id'],))['n'] if r else 0}
    tracked={'update_request','upload','review_document','validity','additional','cancel_requirement','assignment','reception_document','reuse','reopen','resubmit','self_book','appointment_action'}
    @app.before_request
    def capture_before_action():
        if request.method not in ('POST','PATCH') or request.endpoint not in tracked:return
        user=ctx['actor']()
        if not user:return
        args=request.view_args or {};rid=args.get('rid')
        if not rid and args.get('aid'):rid=(one('SELECT request_id FROM appointments WHERE id=?',(args['aid'],)) or {}).get('request_id')
        if not rid and args.get('did'):rid=(one('SELECT request_id FROM documents WHERE id=?',(args['did'],)) or {}).get('request_id')
        if not rid and request.endpoint=='self_book':rid=(request.get_json(silent=True) or {}).get('request_id')
        if type(rid) is not int or rid<1:return
        lock_case(rid);before=snapshot(rid)
        if not before['request']:return
        g.action_before=(rid,before,one('SELECT COALESCE(MAX(id),0) as n FROM events WHERE request_id=?',(rid,))['n'])
    @app.after_request
    def capture_after_action(response):
        if response.status_code>=400 or not getattr(g,'action_before',None):return response
        rid,before,first=g.action_before;after=snapshot(rid)
        events=rows('SELECT id,visibility FROM events WHERE request_id=? AND id>? ORDER BY id',(rid,first))
        target=next((e for e in events if e['visibility']=='public'),events[0] if events else None)
        if target:
            new_appointments={a['id'] for a in after['appointments']} - {a['id'] for a in before['appointments']}
            after['notification_ids']=[n['id'] for n in rows('SELECT id,target FROM notifications WHERE user_id=? AND id>?',(before['request']['user_id'],before['notification_max'])) if n['target'].split('?')[0]==f'/solicitudes/{rid}' or any(n['target']==f'/citas?cita={aid}' for aid in new_appointments)]
            db().execute('INSERT INTO action_history(event_id,last_event_id,request_id,before_json,after_json) VALUES(?,?,?,?,?)',(target['id'],events[-1]['id'],rid,ctx['dumps'](before),ctx['dumps'](after)))
        return response

    def restore_row(table,row):
        fields=[k for k in row if k!='id'];db().execute('UPDATE '+table+' SET '+','.join(k+'=?' for k in fields)+' WHERE id=?',tuple(row[k] for k in fields)+(row['id'],))
    def restore(snapshot_before,current,rid):
        # Keep objects and version rows; only the current selection is reversed.
        before_docs={d['id'] for d in snapshot_before['documents']}
        for d in current['documents']:
            if d['id'] not in before_docs:db().execute('UPDATE documents SET superseded=1 WHERE id=?',(d['id'],))
        for d in snapshot_before['documents']:restore_row('documents',d)
        before_extra={e['id'] for e in snapshot_before['requirements']}
        for e in current['requirements']:
            if e['id'] not in before_extra:db().execute("UPDATE extra_requirements SET active=0,cancel_reason='Solicitud deshecha por el funcionario' WHERE id=?",(e['id'],))
        for e in snapshot_before['requirements']:restore_row('extra_requirements',e)
        before_a={a['id'] for a in snapshot_before['appointments']}
        for a in current['appointments']:
            if a['id'] not in before_a:
                if a['status'] in ('Presente','En atención','Finalizada'):return False
                db().execute("UPDATE appointments SET status='Cancelada' WHERE id=?",(a['id'],))
        for a in snapshot_before['appointments']:
            current_a=next((v for v in current['appointments'] if v['id']==a['id']),None)
            if current_a and current_a['status'] in ('Presente','En atención','Finalizada') and current_a!=a:return False
            restore_row('appointments',a)
        restore_row('requests',snapshot_before['request']);db().execute('UPDATE requests SET updated=? WHERE id=?',(now(),rid))
        return True

    original_edit=app.view_functions['edit_event']
    @auth(staff=True)
    def undo_or_edit(eid):
        if request.method!='DELETE':return original_edit(eid)
        selected=one('SELECT * FROM events WHERE id=? AND deleted_at IS NULL',(eid,));data=request.get_json(silent=True) or {};reason=str(data.get('reason','')).strip()
        if not selected:return fail('Acción no encontrada.',404)
        if not 10<=len(reason)<=2000:return fail('Indica por qué deshaces la acción (10 a 2.000 caracteres).')
        rid=selected['request_id'];lock_case(rid);r=ctx['request_record'](rid)
        if r['status']=='Cerrada' and g.user['role']!='admin':return fail('Solo administración puede deshacer un cierre.',403)
        journal=one('SELECT * FROM action_history WHERE event_id=? AND undone=0 ORDER BY id DESC LIMIT 1',(eid,))
        last=one('SELECT MAX(id) as n FROM events WHERE request_id=? AND deleted_at IS NULL',(rid,))['n']
        limit=journal['last_event_id'] if journal else eid
        if last>limit:return fail('Deshaz primero las acciones posteriores para no alterar cambios que dependen de esta.',409)
        if journal:
            current=snapshot(rid);expected=json.loads(journal['after_json'])
            # A different state may indicate an edit or a later untracked operation.
            if current['request']['status']!=expected['request']['status'] and not one("SELECT id FROM event_edits WHERE event_id=? AND action='edit'",(eid,)):return fail('El expediente cambió después. Revisa su estado antes de deshacer.',409)
            if not restore(json.loads(journal['before_json']),current,rid):return fail('La cita ya registra una atención; no puede deshacerse desde el expediente.',409)
            db().execute('UPDATE action_history SET undone=1 WHERE id=?',(journal['id'],))
            for nid in expected.get('notification_ids',[]):db().execute('UPDATE notifications SET read=1 WHERE id=?',(nid,))
        else:
            # Legacy review events have identifiable document/version and previous review.
            title=selected['status'];note=selected['note'];doc=next((d for d in rows('SELECT * FROM documents WHERE request_id=? AND superseded=0',(rid,)) if note.startswith(str(d['requirement'])+': '+d['name']+'.')),None)
            mapping={'Documento aceptado':'Aceptado','Documento observado':'Rechazado','Documento en revisión':'En revisión'}
            if title in mapping and doc:
                prefix=str(doc['requirement'])+': '+doc['name']+'.'
                previous=next((e for e in rows('SELECT * FROM events WHERE request_id=? AND id<? AND deleted_at IS NULL ORDER BY id DESC',(rid,eid)) if e['status'] in mapping and e['note'].startswith(prefix)),None)
                reviewer=one('SELECT id FROM users WHERE name=?',(previous['actor_name'],)) if previous else None
                db().execute('UPDATE documents SET review_status=?,review_note=?,reviewed_at=?,reviewed_by=? WHERE id=?',(mapping[previous['status']] if previous else 'En revisión',previous['note'][len(prefix):].strip() if previous else None,previous['created'] if previous else None,reviewer['id'] if reviewer else None,doc['id']))
                base={**r,'status':'En revisión'};status='Requiere antecedentes' if ctx['document_overview'](base)['document_tone']=='attention' else 'En revisión'
                db().execute('UPDATE requests SET status=?,updated=? WHERE id=?',(status,now(),rid))
            elif title in ctx['STATUSES']:
                prior=rows('SELECT status FROM events WHERE request_id=? AND id<? AND deleted_at IS NULL ORDER BY id DESC',(rid,eid))
                if not prior:return fail('No existe una acción anterior para restaurar.',409)
                base={**r,'status':'En revisión'};status=next((e['status'] for e in prior if e['status'] in ctx['STATUSES']), 'En revisión')
                if prior[0]['status'] in mapping:status='Requiere antecedentes' if ctx['document_overview'](base)['document_tone']=='attention' else 'En revisión'
                db().execute('UPDATE requests SET status=?,updated=? WHERE id=?',(status,now(),rid))
            else:return fail('Esta acción antigua no tiene un estado anterior completo registrado. Corrígela con el lápiz; las nuevas acciones sí permiten deshacer.',409)
        db().execute('INSERT INTO event_edits(event_id,old_status,old_note,action,reason,actor_id,created) VALUES(?,?,?,?,?,?,?)',(eid,selected['status'],selected['note'],'undo',reason,g.user['id'],now()))
        db().execute('UPDATE events SET deleted_at=? WHERE request_id=? AND id>=? AND id<=?',(now(),rid,eid,limit))
        if selected['visibility']=='public':notify(r['user_id'],'Actualización corregida',r['folio']+': se deshizo la última acción registrada.',f'/solicitudes/{rid}')
        return jsonify(ok=True,undone=True)
    app.view_functions['edit_event']=undo_or_edit

    def valid_day(value):
        try:day=datetime.strptime(value,'%Y-%m-%d').date()
        except (TypeError,ValueError):return None
        today=datetime.now(ZoneInfo('America/Santiago')).date()
        return day if today<=day<=today+timedelta(days=90) and day.weekday()<5 else None
    def free_slots(value):
        if not valid_day(value):return []
        occupied={a['time'] for a in rows("SELECT time FROM appointments WHERE date=? AND status NOT IN ('Cancelada','Finalizada')",(value,))}
        current=datetime.now(ZoneInfo('America/Santiago'))
        return [slot for slot in SLOTS if slot not in occupied and (value>str(current.date()) or slot>current.strftime('%H:%M'))]
    @app.get('/api/appointment-slots')
    @auth()
    def slots():
        value=request.args.get('date','')
        return jsonify(date=value,slots=free_slots(value),opens='09:00',closes='16:00',minutes=30)
    @app.post('/api/appointments/book')
    @auth()
    def self_book():
        if g.user['role']!='citizen':return fail('El ciudadano agenda desde su portal.',403)
        d=request.get_json(silent=True) or {};value=d.get('date');slot=d.get('time');rid=d.get('request_id') or None
        if os.environ.get('DB_HOST'):db().execute('SELECT pg_advisory_xact_lock(742027)')
        else:db().execute('UPDATE users SET active=active WHERE id=?',(g.user['id'],))
        if not valid_day(value) or slot not in free_slots(value):return fail('El bloque no está disponible. Selecciona otro día u horario.',409)
        if one("SELECT id FROM appointments WHERE user_id=? AND date=? AND status NOT IN ('Cancelada','Finalizada')",(g.user['id'],value)):return fail('Ya tienes una cita activa para ese día.',409)
        if rid:
            if type(rid) is not int or rid<1:return fail('Solicitud no válida.')
            r=ctx['request_record'](rid)
            if not r or r['status'] in FINAL:return fail('Selecciona una solicitud tuya que siga abierta.',409)
            if one("SELECT id FROM appointments WHERE request_id=? AND status NOT IN ('Cancelada','Finalizada')",(rid,)):return fail('Esta solicitud ya tiene una cita.',409)
        while True:
            code='CITA-'+str(secrets.randbelow(900000)+100000)
            if not one('SELECT id FROM appointments WHERE code=?',(code,)):break
        aid=db().execute('INSERT INTO appointments(request_id,user_id,date,time,office,status,code,reason,booking_source) VALUES(?,?,?,?,?,?,?,?,?)',(rid,g.user['id'],value,slot,ctx['OFFICE'],'Confirmada',code,str(d.get('reason','')).strip()[:500] or 'Atención presencial','citizen')).lastrowid
        if rid:
            db().execute("UPDATE requests SET status='Cita programada',appointment_requested=0,updated=? WHERE id=?",(now(),rid));event(rid,'Cita programada','El ciudadano reservó un bloque para '+value+' a las '+slot+'.')
        notify(g.user['id'],'Cita confirmada',value+' a las '+slot+'. Código '+code,f'/citas?cita={aid}')
        return jsonify(id=aid,code=code,status='Confirmada'),201
    @auth(staff=True)
    def retired_schedule():return fail('El ciudadano reserva directamente un bloque libre en Mis citas.',410)
    app.view_functions['schedule']=retired_schedule
    app.view_functions['request_appointment']=auth()(lambda rid:fail('Reserva directamente un bloque libre en Mis citas.',410))

    @app.get('/api/reception/day')
    @auth(staff=True)
    def reception_day():
        day=request.args.get('date',now()[:10])
        return jsonify(items=rows("SELECT a.id,a.user_id,a.time,a.status,a.code,COALESCE(u.name,'Visitante sin cita') as owner_name,v.ticket FROM appointments a LEFT JOIN users u ON u.id=a.user_id LEFT JOIN visits v ON v.appointment_id=a.id WHERE a.date=? AND a.status NOT IN ('Cancelada','Finalizada') ORDER BY a.time,a.id",(day,)),date=day)

    @app.get('/api/requests/<int:rid>/certificate')
    @auth()
    def certificate(rid):
        import io
        r=ctx['request_record'](rid)
        if not r:return fail('Solicitud no encontrada.',404)
        if r['status']!='Resuelta':return fail('El certificado está disponible cuando la solicitud está resuelta.',409)
        name=next(x['name'] for x in ctx['CATALOG'] if x['id']==r['type_id'])
        raw=ctx['simple_pdf']('CERTIFICADO - PROTOTIPO ACADEMICO',[name,r['folio'],r['owner_name'],'RUN: '+r['demo_run'][:-1]+'-'+r['demo_run'][-1:],'Fecha: '+now()[:10],'Solicitud resuelta.','Documento de demostracion. Sin validez oficial.'])
        return send_file(io.BytesIO(raw),mimetype='application/pdf',download_name='certificado-'+r['folio']+'.pdf',as_attachment=True)

    @app.get('/api/receptions/<int:aid>')
    @auth(staff=True)
    def guest_detail(aid):
        a=one('SELECT * FROM appointments WHERE id=?',(aid,))
        if not a:return fail('Recepción no encontrada.',404)
        capture=one('SELECT c.id,c.id_name,c.id_mime,c.created,v.ticket FROM reception_captures c JOIN visits v ON v.id=c.visit_id WHERE v.appointment_id=?',(aid,))
        return jsonify(attention=a,capture=capture)
    @app.post('/api/receptions/<int:aid>/link-person')
    @auth(staff=True)
    def link_guest(aid):
        d=request.get_json(silent=True) or {};uid=d.get('user_id');note=str(d.get('note','')).strip()
        a=one('SELECT * FROM appointments WHERE id=?',(aid,))
        if not a or a['user_id']:return fail('Esta recepción ya está vinculada o no existe.',409)
        if a['status']!='En atención' or a['serving_by']!=g.user['id']:return fail('Inicia esta atención antes de vincular la identidad.',409)
        if not one("SELECT id FROM users WHERE id=? AND role='citizen' AND active=1",(uid,)):return fail('Selecciona una persona registrada.')
        if not 10<=len(note)<=500:return fail('Indica cómo contrastaste la identidad (10 a 500 caracteres).')
        if os.environ.get('DB_HOST'):db().execute('SELECT id FROM users WHERE id=? FOR UPDATE',(uid,))
        else:db().execute('UPDATE users SET active=active WHERE id=?',(uid,))
        if one("SELECT id FROM appointments WHERE user_id=? AND status IN ('Presente','En atención') AND id<>?",(uid,aid)):return fail('Esta persona ya tiene otra llegada registrada. Revisa su atención antes de vincular.',409)
        db().execute('UPDATE appointments SET user_id=? WHERE id=?',(uid,aid))
        db().execute('UPDATE reception_captures SET user_id=? WHERE visit_id IN (SELECT id FROM visits WHERE appointment_id=?)',(uid,aid))
        db().execute('INSERT INTO query_log(user_id,person_code,source,result,created) VALUES(?,?,?,?,?)',(g.user['id'],str(uid),'Vinculación presencial',note,now()))
        return jsonify(ok=True,user_id=uid)
