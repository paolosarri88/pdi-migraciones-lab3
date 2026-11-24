"""Fichas ciudadanas, atención presencial y correcciones con trazabilidad."""
import json
import re
import secrets
from datetime import date
from flask import request, jsonify, g

FINAL=('Resuelta','Cerrada','Rechazada')

def install(ctx):
    app,auth,one,rows,db,fail,event,notify,now=(ctx[k] for k in ('app','auth','one','rows','db','fail','event','notify','now'))
    c=ctx['connect'](ctx['DATA'],initialize=True)
    additions={'requests':{'channel':"TEXT DEFAULT 'online'"},'events':{'rectified_reason':'TEXT','rectified_by':'TEXT','rectified_at':'TEXT'},'documents':{'source_document_id':'INTEGER','valid_until':'TEXT'}}
    import os
    for table,cols in additions.items():
        present={r[0] for r in c.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=?",(table,)).fetchall()} if os.environ.get('DB_HOST') else {r[1] for r in c.execute('PRAGMA table_info('+table+')').fetchall()}
        for name,definition in cols.items():
            if name not in present:c.execute('ALTER TABLE '+table+' ADD COLUMN '+name+' '+definition)
    c.executescript('CREATE TABLE IF NOT EXISTS extra_requirements(id INTEGER PRIMARY KEY,request_id INTEGER REFERENCES requests(id),name TEXT,reason TEXT,created TEXT,created_by INTEGER,active INTEGER DEFAULT 1,cancel_reason TEXT);')
    c.commit();c.close()
    def person(uid):return one("SELECT id,name,email,demo_run,nationality,phone,address FROM users WHERE id=? AND role='citizen' AND active=1",(uid,))
    def allowed_person(uid):return g.user['role']!='citizen' or g.user['id']==uid
    def run_text(u):return u['demo_run'][:-1]+'-'+u['demo_run'][-1:]
    def reason(data):return str(data.get('reason','')).strip()
    def open_case(r):return r and r['status'] not in FINAL
    def audit(rid,title,note,kind='correction'):
        event(rid,title,note)
        db().execute('UPDATE events SET kind=? WHERE id=(SELECT MAX(id) FROM events WHERE request_id=?)',(kind,rid))
    @app.get('/api/people/<int:uid>')
    @auth(staff=True)
    def person_detail(uid):
        u=person(uid)
        if not u:return fail('Persona no encontrada.',404)
        u['run']=run_text(u)
        items=rows('SELECT r.*,u.name as owner_name FROM requests r JOIN users u ON u.id=r.user_id WHERE r.user_id=? ORDER BY r.id DESC',(uid,))
        for r in items:r.update(ctx['document_overview'](r));r['ai']=None
        return jsonify(person=u,requests=items)
    @app.post('/api/people')
    @auth(staff=True)
    def create_person():
        # Reuse registration validation and assignment, with role fixed to citizen.
        result=app.view_functions['register']()
        if not isinstance(result,tuple) or result[1]!=201:return result
        payload=result[0].get_json();u=one('SELECT id FROM users WHERE email=?',(payload['email'],))
        data=request.get_json(silent=True) or {}
        db().execute('UPDATE users SET phone=?,address=?,nationality=? WHERE id=?',(str(data.get('phone',''))[:50],str(data.get('address',''))[:300],str(data.get('nationality',''))[:100],u['id']))
        return jsonify(**payload,id=u['id']),201
    @app.post('/api/people/<int:uid>/requests')
    @auth(staff=True)
    def create_presential(uid):
        if not person(uid):return fail('Persona no encontrada.',404)
        d=request.get_json(silent=True) or {};typ=d.get('type_id');description=str(d.get('description','')).strip()
        catalog=next((x for x in ctx['CATALOG'] if x['id']==typ),None)
        if not catalog or not 15<=len(description)<=5000:return fail('Selecciona un trámite y describe la atención (15 a 5.000 caracteres).')
        duplicate=one("SELECT folio FROM requests WHERE user_id=? AND type_id=? AND status NOT IN ('Resuelta','Cerrada','Rechazada')",(uid,typ))
        if duplicate and not catalog['allow_multiple_active']:return fail('Ya existe un expediente activo: '+duplicate['folio'],409)
        cur=db().execute('INSERT INTO requests(user_id,type_id,status,description,details,created,updated,assigned_to,channel) VALUES(?,?,?,?,?,?,?,?,?)',(uid,typ,'En revisión',description,ctx['dumps'](d.get('details',{})),now(),now(),g.user['id'],'presencial'));rid=cur.lastrowid
        folio=f'SOL-{now()[:4]}-{rid:04}';db().execute('UPDATE requests SET folio=? WHERE id=?',(folio,rid))
        audit(rid,'Solicitud presencial registrada',description,'presential-created')
        notify(uid,'Solicitud registrada',folio+': puedes seguirla y aportar documentos en el portal.',f'/solicitudes/{rid}')
        return jsonify(id=rid,folio=folio),201
    @app.get('/api/people/<int:uid>/documents')
    @auth()
    def library(uid):
        if not allowed_person(uid):return fail('No tienes permiso.',403)
        if not person(uid):return fail('Persona no encontrada.',404)
        docs=rows("SELECT d.id,d.name,d.requirement,d.size,d.created,d.valid_until,d.review_status,r.folio FROM documents d JOIN requests r ON r.id=d.request_id WHERE r.user_id=? AND d.superseded=0 ORDER BY d.id DESC",(uid,))
        for d in docs:d['expired']=bool(d['valid_until'] and d['valid_until']<date.fromisoformat(now()[:10]).isoformat())
        return jsonify(items=docs)
    @app.post('/api/requests/<int:rid>/reuse-document')
    @auth()
    def reuse(rid):
        r=ctx['request_record'](rid)
        if not open_case(r):return fail('Expediente no disponible.',409 if r else 404)
        d=request.get_json(silent=True) or {};did=d.get('document_id');name=d.get('requirement')
        source=one('SELECT d.*,r.user_id FROM documents d JOIN requests r ON r.id=d.request_id WHERE d.id=?',(did,))
        if not source or source['user_id']!=r['user_id']:return fail('Documento no disponible para esta persona.',404)
        if source['request_id']==rid:return fail('El archivo ya pertenece a este expediente.',409)
        if source['superseded'] or source['review_status']!='Aceptado':return fail('Solo pueden reutilizarse versiones aceptadas y no reemplazadas.',409)
        if source['valid_until'] and source['valid_until']<now()[:10]:return fail('El documento está vencido. Adjunta una versión vigente.',409)
        if name!=source['requirement'] or name not in [x['name'] for x in ctx['document_groups'](r)]:return fail('El documento no corresponde al requisito seleccionado.')
        current=one('SELECT id,review_status FROM documents WHERE request_id=? AND requirement=? AND superseded=0',(rid,name))
        if current and current['review_status']=='Aceptado':return fail('Este requisito ya está aceptado.',409)
        if one('SELECT COUNT(*) as total FROM documents WHERE request_id=?',(rid,))['total']>=12:return fail('El expediente admite hasta 12 documentos.')
        db().execute('UPDATE documents SET superseded=1 WHERE request_id=? AND requirement=? AND superseded=0',(rid,name))
        cur=db().execute('INSERT INTO documents(request_id,name,path,mime,size,created,requirement,origin,origin_note,source_document_id,valid_until) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(rid,source['name'],source['path'],source['mime'],source['size'],now(),name,'reutilizado','Archivo de '+str(source['request_id'])+'; requiere nueva revisión.',did,source['valid_until']))
        audit(rid,'Documento reutilizado',name+': se incorporó una referencia a la versión existente; pendiente de revisión.','document-reused')
        db().execute('UPDATE requests SET updated=? WHERE id=?',(now(),rid))
        return jsonify(id=cur.lastrowid),201
    @app.patch('/api/documents/<int:did>/validity')
    @auth(staff=True)
    def validity(did):
        doc=one('SELECT * FROM documents WHERE id=?',(did,));d=request.get_json(silent=True) or {};value=d.get('valid_until') or None
        if not doc:return fail('Documento no encontrado.',404)
        r=ctx['request_record'](doc['request_id'])
        if not open_case(r) or doc['superseded']:return fail('Esta versión está cerrada; no se modifica.',409)
        if len(reason(d))<10:return fail('Indica el motivo de la vigencia (mínimo 10 caracteres).')
        if value:
            try:value=date.fromisoformat(value).isoformat()
            except (ValueError,TypeError):return fail('Fecha de vigencia no válida.')
        db().execute('UPDATE documents SET valid_until=? WHERE id=?',(value,did))
        audit(r['id'],'Vigencia documental registrada',doc['requirement']+': '+str(value or 'Sin vencimiento informado')+'. '+reason(d),'document-validity')
        return jsonify(ok=True)
    @app.post('/api/requests/<int:rid>/requirements')
    @auth(staff=True)
    def additional(rid):
        r=ctx['request_record'](rid);d=request.get_json(silent=True) or {};name=d.get('name');note=reason(d)
        if not open_case(r):return fail('Expediente no disponible.',409 if r else 404)
        choices={n for x in ctx['CATALOG'] for n in x['docs']}
        if name not in choices or not 10<=len(note)<=2000:return fail('Selecciona un documento e indica el motivo (10 a 2.000 caracteres).')
        if name in [x['name'] for x in ctx['document_groups'](r)]:return fail('Este documento ya está solicitado.',409)
        cur=db().execute('INSERT INTO extra_requirements(request_id,name,reason,created,created_by) VALUES(?,?,?,?,?)',(rid,name,note,now(),g.user['id']))
        db().execute("UPDATE requests SET status='Requiere antecedentes',updated=? WHERE id=?",(now(),rid))
        audit(rid,'Documento adicional solicitado',name+': '+note,'requirement-added');notify(r['user_id'],'Documento adicional solicitado',name+': '+note,f'/solicitudes/{rid}?accion=adjuntar')
        return jsonify(id=cur.lastrowid),201
    @app.post('/api/requests/<int:rid>/requirements/<int:eid>/cancel')
    @auth(staff=True)
    def cancel_requirement(rid,eid):
        r=ctx['request_record'](rid);d=request.get_json(silent=True) or {};note=reason(d)
        extra=one('SELECT * FROM extra_requirements WHERE id=? AND request_id=? AND active=1',(eid,rid))
        if not open_case(r) or not extra:return fail('Solicitud de documento no disponible.',409)
        if not 10<=len(note)<=2000:return fail('Explica la cancelación (10 a 2.000 caracteres).')
        db().execute('UPDATE extra_requirements SET active=0,cancel_reason=? WHERE id=?',(note,eid))
        db().execute('UPDATE documents SET superseded=1 WHERE request_id=? AND requirement=? AND superseded=0',(rid,extra['name']))
        audit(rid,'Solicitud de documento cancelada',extra['name']+': '+note,'requirement-canceled')
        if not any(x['status'] in ('Falta documento','Rechazado') for x in ctx['document_groups'](r)):
            db().execute("UPDATE requests SET status='En revisión',updated=? WHERE id=?",(now(),rid))
        notify(r['user_id'],'Documento adicional cancelado','Ya no necesitas entregar '+extra['name']+'. '+note,f'/solicitudes/{rid}')
        return jsonify(ok=True)
    @app.post('/api/requests/<int:rid>/reopen')
    @auth(staff=True)
    def reopen(rid):
        r=ctx['request_record'](rid);d=request.get_json(silent=True) or {};note=reason(d)
        if not r:return fail('Expediente no encontrado.',404)
        if r['status'] not in FINAL:return fail('El expediente ya está abierto.',409)
        if r['status']=='Cerrada' and g.user['role']!='admin':return fail('Solo administración puede reabrir un expediente cerrado.',403)
        if not 10<=len(note)<=2000:return fail('Explica por qué se reabre (10 a 2.000 caracteres).')
        old=r['status'];db().execute("UPDATE requests SET status='En revisión',updated=? WHERE id=?",(now(),rid))
        audit(rid,'Expediente reabierto',f'Decisión anterior: {old}. Motivo: {note}','reopened')
        notify(r['user_id'],'Expediente reabierto',r['folio']+': se retomó la revisión. '+note,f'/solicitudes/{rid}')
        return jsonify(ok=True)
    @app.post('/api/events/<int:eid>/rectify')
    @auth(staff=True)
    def rectify(eid):
        e=one('SELECT * FROM events WHERE id=?',(eid,));d=request.get_json(silent=True) or {};note=reason(d)
        if not e:return fail('Registro no encontrado.',404)
        if e['rectified_at']:return fail('Este registro ya fue rectificado.',409)
        if e['kind'] in ('correction','reopened'):return fail('Las correcciones se conservan en el historial.',409)
        if not 10<=len(note)<=2000:return fail('Explica la corrección (10 a 2.000 caracteres).')
        db().execute('UPDATE events SET rectified_reason=?,rectified_by=?,rectified_at=? WHERE id=?',(note,g.user['name'],now(),eid))
        audit(e['request_id'],'Anotación rectificada',f'Registro #{eid} ({e["status"]}): {note}. El estado actual del expediente se conserva.')
        r=ctx['request_record'](e['request_id'])
        notify(r['user_id'],'Anotación rectificada',r['folio']+': '+note,f'/solicitudes/{r["id"]}')
        return jsonify(ok=True)

    @app.post('/api/people/<int:uid>/arrivals')
    @auth(staff=True)
    def arrival(uid):
        if not person(uid):return fail('Persona no encontrada.',404)
        d=request.get_json(silent=True) or {};rid=d.get('request_id')
        if rid:
            r=ctx['request_record'](rid)
            if not r or r['user_id']!=uid or not open_case(r):return fail('Expediente no disponible.',409)
        if one("SELECT id FROM appointments WHERE user_id=? AND status IN ('Presente','En atención')",(uid,)):return fail('Esta persona ya está en la fila o en atención.',409)
        active=one("SELECT id,status FROM appointments WHERE user_id=? AND date=? AND status NOT IN ('Cancelada','Finalizada') ORDER BY id LIMIT 1",(uid,now()[:10]))
        if active:return fail('Esta persona tiene una cita hoy. Registra su llegada desde el tótem con el código de cita.',409)
        cur=db().execute('INSERT INTO appointments(request_id,user_id,date,time,office,status,code,reason) VALUES(?,?,?,?,?,?,?,?)',(rid,uid,now()[:10],now()[11:16],'Atención presencial','Presente','CITA-'+secrets.token_hex(4).upper(),'Atención sin cita registrada por funcionario'))
        aid=cur.lastrowid;ticket=f'A-{aid:03}'
        db().execute('INSERT INTO visits(appointment_id,ticket,entered) VALUES(?,?,?)',(aid,ticket,now()))
        if rid:audit(rid,'Llegada presencial registrada','Turno '+ticket,'arrival')
        return jsonify(id=aid,ticket=ticket),201
