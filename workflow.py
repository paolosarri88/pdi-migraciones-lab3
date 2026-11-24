"""Revisión de antecedentes, recordatorios de calendario y migraciones aditivas."""
import json
import re
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse, parse_qs
from zoneinfo import ZoneInfo
from flask import request, jsonify, g, Response

ctx={}
FINAL=('Resuelta','Cerrada','Rechazada')

def document_groups(record, docs=None):
    if docs is None:docs=ctx['rows']('SELECT * FROM documents WHERE request_id=? ORDER BY id DESC',(record['id'],))
    names=next((x['docs'] for x in ctx['CATALOG'] if x['id']==record['type_id']),[])
    groups=[]
    for name in names:
        matches=[d for d in docs if d.get('requirement')==name and not d.get('superseded')]
        current=max(matches,key=lambda d:d['id']) if matches else None
        groups.append({'name':name,'status':current['review_status'] if current else 'Falta documento','document':current})
    return groups

def document_overview(record,docs=None):
    groups=document_groups(record,docs)
    if record['status'] in FINAL:return {'display_status':record['status'],'document_tone':'rejected' if record['status']=='Rechazada' else 'complete'}
    attention=any(x['status'] in ('Falta documento','Rechazado') for x in groups) or any(d['review_status']=='Rechazado' and not d['superseded'] for d in (docs if docs is not None else ctx['rows']('SELECT * FROM documents WHERE request_id=?',(record['id'],))))
    if attention:return {'display_status':'Requiere antecedentes','document_tone':'attention'}
    return {'display_status':record['status'],'document_tone':'process'}

def active_notices(uid):
    # Actionable notices are derived from current state, never dismissed by reading.
    items=ctx['rows']('SELECT * FROM notifications WHERE user_id=? AND read=0 ORDER BY id DESC',(uid,))
    result=[]
    for r in ctx['rows']('SELECT * FROM requests WHERE user_id=? ORDER BY updated DESC',(uid,)):
        if document_overview(r)['display_status']=='Requiere antecedentes':
            result.append({'id':f"request-{r['id']}",'title':'Antecedentes pendientes','body':f"{r['folio']}: revisa los documentos pendientes u observados y entrega lo solicitado.",'target':f"/solicitudes/{r['id']}?accion=adjuntar",'read':0,'created':r['updated'],'action_required':True})
    for a in ctx['rows']("SELECT * FROM appointments WHERE user_id=? AND status='Pendiente de confirmación' ORDER BY date,time",(uid,)):
        result.append({'id':f"appointment-{a['id']}",'title':'Confirma tu próxima cita','body':f"Atención el {a['date']} a las {a['time']}. Revisa el horario y confirma tu asistencia.",'target':f"/citas?cita={a['id']}",'read':0,'created':a['date'],'action_required':True})
    for n in items:
        u=urlparse(n['target']);q=parse_qs(u.query)
        if q.get('accion')==['adjuntar'] or (u.path=='/citas' and q.get('cita')):continue
        result.append(n)
    return result

def install(context):
    ctx.update(context)
    c=ctx['connect'](ctx['DATA'],initialize=True)
    columns={'visits':{'finished':'TEXT'},'requests':{'appointment_requested':'INTEGER DEFAULT 0'},'users':{'demo_run':'TEXT'},'documents':{'origin':"TEXT DEFAULT 'portal'",'origin_note':'TEXT','ai_review':'TEXT','requirement':'TEXT','review_status':"TEXT DEFAULT 'En revisión'",'review_note':'TEXT','reviewed_at':'TEXT','reviewed_by':'INTEGER','superseded':'INTEGER DEFAULT 0'},'events':{'kind':"TEXT DEFAULT 'status'"},'appointments':{'reminders':"TEXT DEFAULT '[]'",'reminder_phone':"TEXT DEFAULT ''"}}
    import os
    for table, additions in columns.items():
        if os.environ.get('DB_HOST'):
            present={r[0] for r in c.execute('SELECT column_name FROM information_schema.columns WHERE table_schema=\'public\' AND table_name=?',(table,)).fetchall()}
        else:present={r[1] for r in c.execute('PRAGMA table_info('+table+')').fetchall()}
        for name,definition in additions.items():
            if name not in present:c.execute('ALTER TABLE '+table+' ADD COLUMN '+name+' '+definition)
    for old,new in ctx['REQUIREMENT_ALIASES'].items():
        if old!=new:c.execute('UPDATE documents SET requirement=? WHERE requirement=?',(new,old))
    for uid, in c.execute('SELECT id FROM users WHERE demo_run IS NULL').fetchall():
        c.execute('UPDATE users SET demo_run=? WHERE id=?',(f'{uid:08}9',uid))
    for did,rid,typ,status in c.execute('SELECT d.id,r.id,r.type_id,r.status FROM documents d JOIN requests r ON r.id=d.request_id WHERE d.requirement IS NULL ORDER BY d.id').fetchall():
        names=next((x['docs'] for x in ctx['CATALOG'] if x['id']==typ),[])
        used={r[0] for r in c.execute('SELECT requirement FROM documents WHERE request_id=? AND requirement IS NOT NULL',(rid,)).fetchall()}
        name=next((n for n in names if n not in used),'Otros antecedentes')
        c.execute('UPDATE documents SET requirement=?,review_status=? WHERE id=?',(name,'Aceptado' if status in FINAL else 'En revisión',did))
    c.execute('CREATE UNIQUE INDEX IF NOT EXISTS users_demo_run_unique ON users(demo_run)')
    c.commit();c.close()
    app=ctx['app'];auth=ctx['auth'];db=ctx['db'];one=ctx['one'];fail=ctx['fail'];event=ctx['event'];now=ctx['now'];notify=ctx['notify']

    @app.patch('/api/documents/<int:did>/review')
    @auth(staff=True)
    def review_document(did):
        doc=one('SELECT * FROM documents WHERE id=?',(did,))
        if not doc:return fail('Documento no encontrado.',404)
        r=ctx['request_record'](doc['request_id']);d=request.get_json(silent=True) or {}
        status=d.get('status');note=str(d.get('note','')).strip()
        if r['status'] in FINAL:return fail('El expediente ya tiene una decisión final.',409)
        if doc['superseded']:return fail('Este documento tiene un reemplazo más reciente.',409)
        if status not in ('Aceptado','Rechazado','En revisión'):return fail('Estado de revisión no válido.')
        if status=='Rechazado' and len(note)<10:return fail('Explica qué antecedente debe corregir el ciudadano (al menos 10 caracteres).')
        if len(note)>2000:return fail('La observación supera 2.000 caracteres.')
        db().execute('UPDATE documents SET review_status=?,review_note=?,reviewed_at=?,reviewed_by=? WHERE id=?',(status,note,now(),g.user['id'],did))
        groups=document_groups(r)
        needs=document_overview(r)['document_tone']=='attention'
        overall='Requiere antecedentes' if needs else 'Cita programada' if r['status']=='Cita programada' else 'En revisión'
        db().execute('UPDATE requests SET status=?,updated=? WHERE id=?',(overall,now(),r['id']))
        title='Documento aceptado' if status=='Aceptado' else 'Documento observado' if status=='Rechazado' else 'Documento en revisión'
        event(r['id'],title,f"{doc['requirement']}: {doc['name']}. "+(note or 'El funcionario registró la revisión.'))
        kind='document-rejected' if status=='Rechazado' else 'document-accepted' if status=='Aceptado' else 'document-review'
        db().execute('UPDATE events SET kind=? WHERE id=(SELECT MAX(id) FROM events WHERE request_id=?)',(kind,r['id']))
        notify(r['user_id'],title,f"{r['folio']} · {doc['requirement']}. "+(note or 'Consulta el detalle de tu solicitud.'),f"/solicitudes/{r['id']}"+('?accion=adjuntar' if status=='Rechazado' else '')+(''+('&' if status=='Rechazado' else '?')+f'documento={did}'))
        return jsonify(ok=True,status=overall)

    @app.get('/api/document-examples/<key>')
    def document_example(key):
        import io
        from flask import send_file
        from document_rules import DOCUMENT_RULES
        if key not in DOCUMENT_RULES:return fail('Ejemplo no encontrado.',404)
        rule=DOCUMENT_RULES[key]
        lines=['DOCUMENTO FICTICIO. SIN VALIDEZ LEGAL.']+rule['examples']+['Solo para probar el portal academico.']
        return send_file(io.BytesIO(ctx['simple_pdf'](rule['title'],lines)),mimetype='application/pdf',download_name='ejemplo-'+key+'.pdf',as_attachment=True)

    @app.post('/api/requests/<int:rid>/appointment-request')
    @auth()
    def request_appointment(rid):
        r=ctx['request_record'](rid)
        if not r:return fail('Solicitud no encontrada.',404)
        if g.user['role']!='citizen':return fail('Esta opción corresponde al portal ciudadano.',403)
        if r['status'] in FINAL:return fail('El expediente está cerrado. Inicia una nueva solicitud si necesitas otra atención.',409)
        if r['appointment_requested']:return fail('Ya solicitaste atención para este expediente. El funcionario debe coordinarla.',409)
        if one("SELECT id FROM appointments WHERE request_id=? AND status NOT IN ('Cancelada','Finalizada')",(rid,)):return fail('Ya tienes una cita vigente para este expediente. Revísala en Mis citas.',409)
        note=str((request.get_json(silent=True) or {}).get('reason','')).strip()
        if len(note)>1000:return fail('El motivo no puede superar 1.000 caracteres.')
        db().execute('UPDATE requests SET appointment_requested=1,updated=? WHERE id=?',(now(),rid))
        event(rid,r['status'],'El ciudadano solicitó atención presencial. '+(note or 'Coordinación de atención para este expediente.'))
        db().execute("UPDATE events SET kind='appointment-request' WHERE id=(SELECT MAX(id) FROM events WHERE request_id=?)",(rid,))
        for u in ctx['rows']("SELECT id FROM users WHERE role IN ('staff','admin') AND active=1"):
            notify(u['id'],'Solicitud de atención presencial',r['folio']+': revisar y coordinar una cita.',f'/expedientes/{rid}')
        return jsonify(ok=True),201

    @app.patch('/api/appointments/<int:aid>/reminders')
    @auth()
    def reminders(aid):
        a=one('SELECT * FROM appointments WHERE id=?',(aid,))
        if not a or (g.user['role']=='citizen' and a['user_id']!=g.user['id']):return fail('Cita no encontrada.',404)
        if a['status'] not in ('Confirmada','Presente'):return fail('Confirma la cita antes de configurar recordatorios.',409)
        data=request.get_json(silent=True) or {};minutes=data.get('minutes',[]);phone=str(data.get('phone','')).strip()
        if not isinstance(minutes,list) or any(type(v) is not int or v not in (5,10,30,60,600,1440) for v in minutes):return fail('Selecciona los plazos disponibles.')
        if len(phone)>30 or (phone and not re.fullmatch(r'[+0-9 ()-]{6,30}',phone)):return fail('Teléfono de prueba no válido.')
        db().execute('UPDATE appointments SET reminders=?,reminder_phone=? WHERE id=?',(json.dumps(sorted(set(minutes))),phone,aid))
        return jsonify(ok=True,sms_enabled=False)

    @app.get('/api/appointments/<int:aid>/calendar')
    @auth()
    def calendar(aid):
        a=one('SELECT * FROM appointments WHERE id=?',(aid,))
        if not a or (g.user['role']=='citizen' and a['user_id']!=g.user['id']):return fail('Cita no encontrada.',404)
        if a['status'] not in ('Confirmada','Presente'):return fail('La cita debe estar confirmada.',409)
        def stamp(t):return t.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        def text(v):return str(v).replace('\\','\\\\').replace('\r','').replace('\n','\\n').replace(';','\\;').replace(',','\\,')
        start=datetime.fromisoformat(a['date']+'T'+a['time']).replace(tzinfo=ZoneInfo('America/Santiago'))
        lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//UAI//PDI Demo//ES','CALSCALE:GREGORIAN','BEGIN:VEVENT',f"UID:pdi-demo-{aid}@portal.local",'DTSTAMP:'+stamp(datetime.now(timezone.utc)),'DTSTART:'+stamp(start),'DTEND:'+stamp(start+timedelta(minutes=30)),'SUMMARY:Atención migratoria - demostración','LOCATION:'+text(a['office']),'DESCRIPTION:'+text('Código: '+a['code']+'. Prototipo académico; no corresponde a una cita real PDI.')]
        for mins in json.loads(a['reminders'] or '[]'):lines.extend(['BEGIN:VALARM',f'TRIGGER:-PT{int(mins)}M','ACTION:DISPLAY','DESCRIPTION:Recordatorio de cita de demostración','END:VALARM'])
        lines.extend(['END:VEVENT','END:VCALENDAR',''])
        # Fold UTF-8 lines at <=75 octets according to RFC 5545.
        folded=[]
        for line in lines:
            chunk='';size=0
            for char in line:
                n=len(char.encode('utf-8'))
                if size+n>74:folded.append(chunk);chunk=' ';size=1
                chunk+=char;size+=n
            folded.append(chunk)
        return Response('\r\n'.join(folded),mimetype='text/calendar',headers={'Content-Disposition':f'attachment; filename="cita-{aid}.ics"'})
