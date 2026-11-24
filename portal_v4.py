"""Cuentas ciudadanas, identificadores y bandeja de trabajo del funcionario."""
import re
import secrets
from datetime import datetime
from flask import request,jsonify,g,send_from_directory

def install(ctx):
    app,auth,one,rows,db,fail=(ctx[k] for k in ('app','auth','one','rows','db','fail'))
    def format_run(run):return run[:-1]+'-'+run[-1:] if run else ''
    def accounts():
        return [{**u,'run':format_run(u['demo_run'])} for u in rows("SELECT id,name,email,role,demo_run FROM users WHERE id<=15 AND email LIKE '%@demo.pdi.cl' AND active=1 ORDER BY id")]
    @app.get('/api/demo-accounts')
    def demo_accounts():return jsonify(items=accounts())

    @app.post('/api/register')
    def register():
        data=request.get_json(silent=True) or {};name=str(data.get('name','')).strip();email=str(data.get('email','')).strip().lower();password=str(data.get('password',''))
        if not 3<=len(name)<=100:return fail('Ingresa un nombre de entre 3 y 100 caracteres.')
        if len(email)>150 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email):return fail('Ingresa un correo válido.')
        if not 10<=len(password)<=128:return fail('La clave debe tener entre 10 y 128 caracteres.')
        if one('SELECT id FROM users WHERE email=?',(email,)):return fail('Ese correo ya tiene una cuenta.',409)
        # Assigned synthetic identifier, no need to collect a real government ID.
        while True:
            number='99'+str(secrets.randbelow(1000000)).zfill(6)
            total=sum(int(n)*((i%6)+2) for i,n in enumerate(reversed(number)));dv=11-total%11
            run=number+('0' if dv==11 else 'K' if dv==10 else str(dv))
            if not one('SELECT id FROM users WHERE demo_run=?',(run,)):break
        cur=db().execute("INSERT INTO users(name,email,password,role,document,nationality,phone,address,demo_run) VALUES(?,?,?,?,?,?,?,?,?)",(name,email,ctx['generate_password_hash'](password),'citizen',format_run(run),'','','',run))
        db().execute('INSERT INTO institutional(person_code,user_id,identity_status,migration_status,entry_date,border,notes) VALUES(?,?,?,?,?,?,?)',(format_run(run),cur.lastrowid,'Identidad registrada','Sin antecedentes ingresados',None,'','Registro de simulación.'))
        return jsonify(ok=True,run=format_run(run),email=email),201

    @app.get('/api/workboard')
    @auth(staff=True)
    def workboard():
        queue=rows("SELECT a.*,COALESCE(u.name,'Visitante sin cita') as owner_name,r.folio,v.ticket,v.entered,v.started,s.name as serving_name FROM appointments a LEFT JOIN users u ON u.id=a.user_id LEFT JOIN requests r ON r.id=a.request_id LEFT JOIN visits v ON v.appointment_id=a.id LEFT JOIN users s ON s.id=a.serving_by WHERE a.status IN ('Presente','En atención') ORDER BY CASE WHEN a.status='En atención' THEN 0 ELSE 1 END,v.entered,a.id")
        cases=rows("SELECT r.*,u.name as owner_name FROM requests r JOIN users u ON u.id=r.user_id WHERE r.status NOT IN ('Resuelta','Cerrada','Rechazada') ORDER BY r.created,r.id")
        tasks=[]
        active_citations={a['request_id'] for a in rows("SELECT request_id FROM appointments WHERE status NOT IN ('Cancelada','Finalizada')")}
        for r in cases:
            docs=rows('SELECT * FROM documents WHERE request_id=? AND superseded=0',(r['id'],))
            count=sum(d['review_status']=='En revisión' for d in docs)
            if r['appointment_requested']:action='Coordinar cita';priority=0
            elif count:action=f'Revisar {count} documento'+('s' if count!=1 else '');priority=1
            elif ctx['document_overview'](r,docs)['display_status']=='Requiere antecedentes':action='Esperar antecedentes';priority=4
            elif r['status']=='Cita programada' and r['id'] in active_citations:action='Atención programada';priority=3
            else:action='Resolver expediente';priority=2
            tasks.append({'id':r['id'],'folio':r['folio'],'owner_name':r['owner_name'],'channel':r.get('channel','online'),'action':action,'priority':priority,'pending_documents':count})
        tasks.sort(key=lambda t:t['priority'])
        return jsonify(queue=queue,tasks=tasks,priority_policy='Atención en curso, luego personas en espera por orden de llegada; después revisión de expedientes.')

    @app.get('/api/institutional/people')
    @auth(staff=True)
    def institutional_people():
        return jsonify(items=[{'id':u['id'],'name':u['name'],'run':format_run(u['demo_run']),'passport':f"PAS-{u['id']:06}"} for u in rows("SELECT id,name,demo_run FROM users WHERE role='citizen' AND active=1 ORDER BY name")])

    @app.post('/api/simulators/<source>/query')
    @auth(staff=True)
    def query_simulator(source):
        import unicodedata
        if source not in ('gepol','registro-civil'):return fail('Sistema no encontrado.',404)
        d=request.get_json(silent=True) or {};run=str(d.get('run','')).strip();name=str(d.get('name','')).strip();passport=str(d.get('passport','')).strip().upper()
        if run and not re.fullmatch(r'\d{7,8}-[0-9kK]',run):return fail('Formato de RUN: 12345678-9, sin puntos y con guion.')
        if not any((run,name,passport)):return fail('Ingresa RUN, nombre o pasaporte.')
        def norm(v):return ''.join(c for c in unicodedata.normalize('NFD',v.lower()) if not unicodedata.combining(c))
        records=rows("SELECT u.id,u.name,u.demo_run,u.nationality,u.alias,u.birth_info,u.birthplace,i.criminal_status,i.criminal_notes,i.identity_status,i.migration_status,i.entry_date,i.border,i.notes FROM users u LEFT JOIN institutional i ON i.user_id=u.id WHERE u.role='citizen' AND u.active=1 ORDER BY u.name")
        found=[]
        for u in records:
            pr=f"PAS-{u['id']:06}"
            if run and u['demo_run']!=run.replace('-','').upper():continue
            if name and norm(name) not in norm(u['name']):continue
            if passport and passport!=pr:continue
            item={'name':u['name'],'run':format_run(u['demo_run']),'passport':pr,'identity_status':u['identity_status'] or 'Sin registro','nationality':u['nationality'] or 'No informada','alias':u['alias'] or 'Sin alias','birth_info':u['birth_info'] or 'No informado','birthplace':u['birthplace'] or 'No informado'}
            if source=='gepol':item.update(migration_status=u['migration_status'] or 'Sin registro',entry_date=u['entry_date'],border=u['border'] or 'No informado',notes=u['notes'] or '',criminal_status=u['criminal_status'] or 'Sin información',criminal_notes=u['criminal_notes'] or '')
            found.append(item)
        db().execute('INSERT INTO query_log(user_id,person_code,source,result,created) VALUES(?,?,?,?,?)',(g.user['id'],run or passport or name[:100],'GEPOL' if source=='gepol' else 'Registro Civil',f'{len(found)} resultado(s)',ctx['now']()))
        return jsonify(items=found,simulated=True)

    @app.get('/simuladores/gepol')
    @app.get('/simuladores/registro-civil')
    def simulator_page():return send_from_directory(ctx['ROOT']/'static','institutional-simulator.html')

    @app.get('/totem')
    def kiosk_page():return send_from_directory(ctx['ROOT']/'static','kiosk.html')
