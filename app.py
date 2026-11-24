"""Portal académico PDI. Persistencia local SQLite; sin conexión institucional real."""
from __future__ import annotations
import base64
import hashlib
import io
import json
import os
import re
import secrets
import sqlite3
import time
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from zoneinfo import ZoneInfo
from flask import Flask, g, jsonify, request, session, send_file, send_from_directory
from document_rules import help_for_catalog
from document_ai import inspect_document, enabled as document_ai_enabled, configured as document_ai_configured
from werkzeug.security import check_password_hash, generate_password_hash
from persistence import connect, get_document, put_document

ROOT = Path(__file__).parent
DATA = Path(os.environ.get('PDI_DATA_DIR', ROOT / 'data'))
DATA.mkdir(parents=True, exist_ok=True)
(DATA / 'files').mkdir(exist_ok=True)
keyfile = DATA / '.session-key'
if not keyfile.exists():
    keyfile.write_text(secrets.token_hex(32)); keyfile.chmod(0o600)
app = Flask(__name__, static_folder='static')
app.config.update(SECRET_KEY=os.environ.get('SECRET_KEY', keyfile.read_text()), MAX_CONTENT_LENGTH=9*1024*1024,
                  SESSION_COOKIE_SECURE=os.environ.get('CLOUD_DEPLOYMENT')=='1', SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', PERMANENT_SESSION_LIFETIME=timedelta(hours=8))
STATUSES = ['Recibida', 'En revisión', 'Requiere antecedentes', 'Cita programada', 'Resuelta', 'Cerrada', 'Rechazada']
OFFICE = 'Migraciones y Policía Internacional · Santiago'
SOURCE = 'https://www.pdichile.cl/tr%C3%A1mites-online'
CATALOG = [
 {'id':'viajes','name':'Certificado de viajes','group':'Certificados','description':'Consulta y acreditación de movimientos de entrada y salida del país.','docs':['Documento de identidad de prueba','Antecedente del viaje, si corresponde'],'fields':['País o institución donde se presentará','Período de viajes a consultar'],'source':'https://www.pdichile.cl/tr%C3%A1mites-online'},
 {'id':'vigencia-rm','name':'Vigencia de residencia definitiva · RM','group':'Certificados','description':'Demostración de revisión de antecedentes de residencia para la Región Metropolitana.','docs':['Documento de identidad de prueba','Antecedente de residencia de prueba'],'fields':['Comuna de residencia','Institución donde presentarás el certificado'],'source':'https://www.pdichile.cl/tr%C3%A1mites-online/vigencia-residencia-definitiva-rm'},
 {'id':'vigencia-regiones','name':'Vigencia de residencia definitiva · Regiones','group':'Certificados','description':'Demostración de una solicitud de vigencia fuera de la Región Metropolitana.','docs':['Documento de identidad de prueba','Antecedente de residencia de prueba'],'fields':['Región de residencia','Comuna de residencia'],'source':'https://www.pdichile.cl/tr%C3%A1mites-online/Vigencia-Residencia-Definitiva-Regiones'},
 {'id':'duplicado-visa','name':'Duplicado del registro de visa','group':'Duplicados','description':'Solicitud de demostración para obtener una copia de un registro previo.','docs':['Documento de identidad de prueba','Antecedente del registro, si se dispone'],'fields':['Año aproximado del registro','Motivo del duplicado'],'source':'https://www.pdichile.cl/instituci%C3%B3n/unidades/migraciones'},
 {'id':'tarjeta-turismo','name':'Duplicado de tarjeta de turismo','group':'Duplicados','description':'Simulación del ingreso de antecedentes para recuperar un registro de turismo.','docs':['Documento de viaje de prueba'],'fields':['Fecha aproximada de ingreso','Paso fronterizo'],'source':'https://www.pdichile.cl/tr%C3%A1mites-online'},
 {'id':'perdida','name':'Constancia de pérdida de documento','group':'Constancias','description':'Demostración de una constancia relativa a un documento de identidad extranjero.','docs':['Identificación o antecedente alternativo de prueba'],'fields':['Tipo de documento extraviado','Circunstancias del extravío'],'source':'https://www.pdichile.cl/tr%C3%A1mites-online/constancia-de-p%C3%A9rdida-de-documento'},
 {'id':'domicilio','name':'Certificado de residencia y domicilio','group':'Certificados','description':'Demostración de revisión de domicilio y antecedentes asociados.','docs':['Documento de identidad de prueba','Antecedente de domicilio de prueba'],'fields':['Dirección declarada','Comuna'],'source':'https://www.pdichile.cl/instituci%C3%B3n/unidades/migraciones'},
 {'id':'registro-ingreso','name':'Revisión de registro de ingreso','group':'Atención migratoria','description':'Caso académico basado en la visita a PDI: antecedentes de ingreso no encontrados o incompletos.','docs':['Documento de viaje de prueba','Antecedente de ingreso de prueba'],'fields':['Fecha declarada de ingreso','Paso fronterizo declarado'],'source':None},
 {'id':'antecedentes','name':'Entrega de antecedentes complementarios','group':'Atención migratoria','description':'Caso académico para asociar antecedentes adicionales a una revisión institucional.','docs':['Antecedente complementario de prueba'],'fields':['Folio relacionado','Detalle del antecedente'],'source':None},
 {'id':'entrevista','name':'Coordinación de entrevista presencial','group':'Atención migratoria','description':'Caso académico para coordinar la entrega y revisión de antecedentes que requieran atención presencial.','docs':['Documento de identidad de prueba'],'fields':['Motivo de atención','Disponibilidad horaria'],'source':None},
 {'id':'orientacion','name':'Orientación migratoria','group':'Atención migratoria','description':'Solicitud de orientación y derivación dentro de la demostración.','docs':[],'fields':['Tema de la consulta'],'source':None},
]
# Display labels are canonical; retain aliases to migrate existing document slots.
REQUIREMENT_ALIASES={name:name.replace(' de prueba','') for c in CATALOG for name in c['docs']}
for c in CATALOG:
    c['docs']=[REQUIREMENT_ALIASES[n] for n in c['docs']]
    c['name']=c['name'].replace(' · ',' - ')
    c['allow_multiple_active']=c['id'] in ('viajes','domicilio')
DESCRIPTIONS={'vigencia-rm':'Consulta de vigencia de residencia definitiva en la Región Metropolitana.','vigencia-regiones':'Consulta de vigencia de residencia definitiva en regiones.','duplicado-visa':'Obtén una copia de un registro anterior.','tarjeta-turismo':'Presenta los antecedentes para recuperar un registro de turismo.','perdida':'Informa la pérdida de un documento de identidad extranjero.','domicilio':'Presenta antecedentes de residencia y domicilio.','registro-ingreso':'Solicita revisión de un ingreso no encontrado o incompleto.','antecedentes':'Presenta antecedentes adicionales para una revisión.','entrevista':'Solicita coordinación de una entrevista presencial.','orientacion':'Consulta y recibe orientación sobre tu situación migratoria.'}
for c in CATALOG:c['description']=DESCRIPTIONS.get(c['id'],c['description'])

EXTERNAL = [
 {'name':'Salvoconducto','description':'Revisa el procedimiento y las condiciones en el portal oficial.','url':'https://www.pdichile.cl/tr%C3%A1mites-online/salvoconducto'},
 {'name':'AutoSeguro','description':'Servicio institucional externo al alcance migratorio del prototipo.','url':'https://www.autoseguro.gob.cl'},
 {'name':'Denunciar un delito','description':'Consulta los canales oficiales. Esta aplicación no recibe denuncias reales.','url':'https://www.pdichile.cl/informaci%C3%B3n/denuncia-seguro'},
 {'name':'Permisos de residencia y nacionalización','description':'Orientación hacia el Servicio Nacional de Migraciones; no se tramitan aquí.','url':'https://serviciomigraciones.cl/'},
]

def now(): return datetime.now(ZoneInfo('America/Santiago')).isoformat(timespec='seconds')
def dumps(x): return json.dumps(x, ensure_ascii=False)
def db():
    if 'db' not in g:
        g.db = connect(DATA)
        g.db.row_factory=sqlite3.Row
    return g.db
def rows(sql,args=()): return [dict(r) for r in db().execute(sql,args).fetchall()]
def one(sql,args=()):
    r=db().execute(sql,args).fetchone(); return dict(r) if r else None
def fail(message, code=400): return jsonify(error=message),code
def actor(): return one('SELECT id,name,email,role,document,demo_run,nationality,phone,address FROM users WHERE id=? AND active=1',(session.get('uid',-1),))
def auth(staff=False,admin=False):
    def deco(fn):
        @wraps(fn)
        def wrap(*a,**kw):
            u=actor()
            if not u:return fail('Inicia sesión para continuar.',401)
            if (staff and u['role'] not in ('staff','admin')) or (admin and u['role']!='admin'):return fail('No tienes permiso para realizar esta acción.',403)
            g.user=u
            return fn(*a,**kw)
        return wrap
    return deco
def request_record(rid):
    r=one('SELECT r.*,u.name as owner_name,u.document,u.demo_run,u.email FROM requests r JOIN users u ON u.id=r.user_id WHERE r.id=?',(rid,))
    if r and (g.user['role'] in ('staff','admin') or r['user_id']==g.user['id']):return r
    return None
def event(rid,status,note,visibility='public'):
    db().execute('INSERT INTO events(request_id,status,note,actor_name,created,visibility) VALUES(?,?,?,?,?,?)',(rid,status,note,g.user['name'],now(),visibility))
def notify(uid,title,body,target):
    db().execute('INSERT INTO notifications(user_id,title,body,target,created) VALUES(?,?,?,?,?)',(uid,title,body,target,now()))
def simple_pdf(title,lines):
    def esc(s):return s.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    content='BT /F1 18 Tf 55 780 Td ('+esc(title)+') Tj /F1 11 Tf '
    for line in lines:content+='0 -24 Td ('+esc(line)+') Tj '
    content+='ET';raw=content.encode('latin-1','replace')
    objs=[b'<< /Type /Catalog /Pages 2 0 R >>',b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',b'<< /Length '+str(len(raw)).encode()+b' >>\nstream\n'+raw+b'\nendstream']
    out=b'%PDF-1.4\n';offsets=[0]
    for i,obj in enumerate(objs,1):offsets.append(len(out));out+=f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n'
    start=len(out);out+=f'xref\n0 {len(objs)+1}\n0000000000 65535 f \n'.encode()
    out+=b''.join(f'{o:010d} 00000 n \n'.encode() for o in offsets[1:])
    return out+f'trailer\n<< /Size {len(objs)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF'.encode()

def init():
    c=connect(DATA, initialize=True)
    c.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT,email TEXT UNIQUE,password TEXT,role TEXT,document TEXT,nationality TEXT,phone TEXT,address TEXT,active INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS requests(id INTEGER PRIMARY KEY,folio TEXT UNIQUE,user_id INTEGER REFERENCES users(id),type_id TEXT,status TEXT,description TEXT,details TEXT,created TEXT,updated TEXT,assigned_to INTEGER REFERENCES users(id),ai TEXT);
    CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY,request_id INTEGER REFERENCES requests(id),status TEXT,note TEXT,actor_name TEXT,created TEXT,visibility TEXT DEFAULT 'public');
    CREATE TABLE IF NOT EXISTS documents(id INTEGER PRIMARY KEY,request_id INTEGER REFERENCES requests(id),name TEXT,path TEXT,mime TEXT,size INTEGER,created TEXT);
    CREATE TABLE IF NOT EXISTS appointments(id INTEGER PRIMARY KEY,request_id INTEGER REFERENCES requests(id),user_id INTEGER REFERENCES users(id),date TEXT,time TEXT,office TEXT,status TEXT,code TEXT UNIQUE,reason TEXT);
    CREATE UNIQUE INDEX IF NOT EXISTS appointment_slot ON appointments(date,time) WHERE status NOT IN ('Cancelada','Finalizada');
    CREATE TABLE IF NOT EXISTS visits(id INTEGER PRIMARY KEY,appointment_id INTEGER REFERENCES appointments(id),ticket TEXT,entered TEXT,started TEXT,exited TEXT);
    CREATE UNIQUE INDEX IF NOT EXISTS one_visit ON visits(appointment_id);
    CREATE TABLE IF NOT EXISTS notifications(id INTEGER PRIMARY KEY,user_id INTEGER REFERENCES users(id),title TEXT,body TEXT,target TEXT,created TEXT,read INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS institutional(id INTEGER PRIMARY KEY,person_code TEXT UNIQUE,user_id INTEGER REFERENCES users(id),identity_status TEXT,migration_status TEXT,entry_date TEXT,border TEXT,notes TEXT);
    CREATE TABLE IF NOT EXISTS query_log(id INTEGER PRIMARY KEY,user_id INTEGER,person_code TEXT,source TEXT,result TEXT,created TEXT);
    ''')
    if c.execute('SELECT COUNT(*) FROM users').fetchone()[0]:c.commit();c.close();return
    people=[('María Fernanda Rojas','ciudadano@demo.pdi.cl','Ciudadano2026!','citizen','DEMO-001','Perú'),('Javier Morales','funcionario@demo.pdi.cl','Funcionario2026!','staff','FUNC-001','Chile'),('Paolo Sarri','admin@demo.pdi.cl','Admin2026!','admin','ADMIN-001','Chile')]
    names=['Andrés Pérez','Valentina Castro','Lucía Torres','Diego Méndez','Camila Fuentes','Gabriel Silva','Sofía Mendoza','Mateo Ramírez','Isabel Soto','Nicolás Herrera','Daniela López','Tomás Rivas']
    for i,n in enumerate(names):people.append((n,f'persona{i+2}@demo.pdi.cl','Ciudadano2026!','citizen',f'DEMO-{i+2:03}', ['Argentina','Colombia','Venezuela','Bolivia'][i%4]))
    for name,email,pw,role,doc,nat in people:c.execute('INSERT INTO users(name,email,password,role,document,nationality,phone,address) VALUES(?,?,?,?,?,?,?,?)',(name,email,generate_password_hash(pw),role,doc,nat,'+56 9 0000 0000','Domicilio ficticio · Santiago'))
    today=datetime.now(ZoneInfo('America/Santiago')).date()
    scenarios=[(1,'viajes','En revisión','Necesito presentar mis movimientos migratorios para un trámite personal.'),(1,'registro-ingreso','Requiere antecedentes','No aparece mi último ingreso por el paso fronterizo. Solicito revisión.'),(1,'vigencia-rm','Cita programada','Quiero revisar los antecedentes de mi residencia.'),(1,'perdida','Resuelta','Extravié un documento de identidad de mi país de origen.'),(1,'domicilio','Cerrada','Necesito presentar un antecedente de mi domicilio.'),(1,'orientacion','Recibida','Quisiera orientación sobre la documentación de un viaje.')]
    citizen_ids=[r[0] for r in c.execute("SELECT id FROM users WHERE role='citizen' AND id!=1")]
    for i in range(30):scenarios.append((citizen_ids[i%len(citizen_ids)],CATALOG[i%len(CATALOG)]['id'],STATUSES[i%6],f'Antecedentes de demostración para la solicitud {i+7}.'))
    for i,(uid,typ,status,desc) in enumerate(scenarios,1):
        created=f'{today-timedelta(days=2+i%14)}T09:15:00-03:00';folio=f'SOL-{today.year}-{i:04}'
        c.execute('INSERT INTO requests(id,folio,user_id,type_id,status,description,details,created,updated,assigned_to) VALUES(?,?,?,?,?,?,?,?,?,?)',(i,folio,uid,typ,status,desc,dumps({'Información declarada':'Antecedentes ficticios para la demostración'}),created,created,2 if i%3 else None))
        c.execute('INSERT INTO events(request_id,status,note,actor_name,created) VALUES(?,?,?,?,?)',(i,'Recibida','Solicitud ingresada al portal.','Sistema de demostración',created))
        if status!='Recibida':c.execute('INSERT INTO events(request_id,status,note,actor_name,created) VALUES(?,?,?,?,?)',(i,status,'Adjunta un antecedente de ingreso complementario.' if status=='Requiere antecedentes' else 'Se actualizó el estado de tu solicitud.','Javier Morales',f'{today-timedelta(days=1)}T11:00:00-03:00'))
        raw=simple_pdf('DOCUMENTO DE DEMOSTRACION',[folio,'Datos ficticios. Sin validez legal.',desc[:85]])
        path=f'seed-{i}.pdf';put_document(DATA,path,raw)
        c.execute('INSERT INTO documents(request_id,name,path,mime,size,created) VALUES(?,?,?,?,?,?)',(i,'antecedente_demo.pdf',path,'application/pdf',len(raw),created))
    appts=[(3,1,today+timedelta(days=2),'10:30','Pendiente de confirmación','CITA-1001'),(7,citizen_ids[0],today,'09:00','Confirmada','CITA-1002'),(8,citizen_ids[1],today,'09:30','Presente','CITA-1003'),(9,citizen_ids[2],today,'10:00','En atención','CITA-1004'),(1,1,today+timedelta(days=4),'11:00','Confirmada','CITA-1005')]
    for rid,uid,date,tm,status,code in appts:
        aid=c.execute('INSERT INTO appointments(request_id,user_id,date,time,office,status,code,reason) VALUES(?,?,?,?,?,?,?,?)',(rid,uid,str(date),tm,OFFICE,status,code,'Revisión de antecedentes de demostración')).lastrowid
        if status in ('Presente','En atención'):c.execute('INSERT INTO visits(appointment_id,ticket,entered,started) VALUES(?,?,?,?)',(aid,f'A-{aid:03}',now(),now() if status=='En atención' else None))
    c.execute('INSERT INTO notifications(user_id,title,body,target,created) VALUES(?,?,?,?,?)',(1,'Antecedentes pendientes','Adjunta el antecedente solicitado para continuar la revisión.','/solicitudes/2?accion=adjuntar',now()))
    c.execute('INSERT INTO notifications(user_id,title,body,target,created) VALUES(?,?,?,?,?)',(1,'Confirma tu próxima cita','Revisa el horario y confirma tu asistencia.','/citas?cita=1',now()))
    for uid,doc in c.execute("SELECT id,document FROM users WHERE role='citizen'").fetchall():
        missing=uid%3==1
        c.execute('INSERT INTO institutional(person_code,user_id,identity_status,migration_status,entry_date,border,notes) VALUES(?,?,?,?,?,?,?)',(doc,uid,'Identidad ficticia registrada','Registro incompleto' if missing else 'Registro encontrado',None if missing else str(today-timedelta(days=100)), 'Los Libertadores' if uid%2 else 'Aeropuerto de Santiago','Caso simulado. No se consultan antecedentes reales.'))
    if os.environ.get('DB_HOST'):c.reset_sequences()
    c.commit();c.close()

@app.before_request
def before():
    if request.path.startswith('/api/') and request.method in ('POST','PUT','PATCH','DELETE'):
        token=session.get('csrf')
        if not token or not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),token):return fail('La sesión de seguridad venció. Recarga la página.',403)

@app.after_request
def after(resp):
    if 'db' in g:
        if resp.status_code<400:g.db.commit()
        else:g.db.rollback()
    resp.headers['X-Content-Type-Options']='nosniff'
    resp.headers['Referrer-Policy']='same-origin'
    resp.headers['X-Frame-Options']='SAMEORIGIN'
    if request.path.startswith('/api/'):resp.headers['Cache-Control']='no-store'
    return resp

@app.teardown_appcontext
def close(_):
    if 'db' in g:g.db.close()

@app.errorhandler(413)
def too_big(_):return fail('El archivo supera el tamaño permitido (5 MB).',413)

@app.errorhandler(sqlite3.IntegrityError)
def conflict(_):return fail('La operación entra en conflicto con un registro existente. Actualiza la vista.',409)

if os.environ.get('DB_HOST'):
    import psycopg
    app.register_error_handler(psycopg.IntegrityError, conflict)

@app.get('/api/bootstrap')
def bootstrap():
    if 'csrf' not in session:session['csrf']=secrets.token_urlsafe(32)
    return jsonify(user=actor(),csrf=session['csrf'],catalog=CATALOG,document_help=help_for_catalog(CATALOG),external=EXTERNAL,statuses=STATUSES,document_ai_available=document_ai_enabled(),ai_available=all(os.environ.get(k) for k in ('AZURE_OPENAI_ENDPOINT','AZURE_OPENAI_API_KEY','AZURE_OPENAI_DEPLOYMENT')),today=str(datetime.now(ZoneInfo('America/Santiago')).date()))

attempts={}
@app.post('/api/login')
def login():
    data=request.get_json(silent=True) or {};email=str(data.get('email','')).strip().lower();ip=request.remote_addr
    attempts[ip]=[t for t in attempts.get(ip,[]) if time.time()-t<60]
    if len(attempts[ip])>=12:return fail('Demasiados intentos. Espera un minuto.',429)
    access=data.get('access')
    if '@' not in email and not re.fullmatch(r'\d{7,8}-[0-9kK]',email):return fail('Formato de RUN: 12345678-9, sin puntos y con guion.',400)
    if access=='staff' and '@' not in email:return fail('Ingresa tu correo corporativo.',400)
    identifier=''.join(ch for ch in email.upper() if ch.isalnum())
    u=one('SELECT * FROM users WHERE (email=? OR demo_run=?) AND active=1',(email,identifier))
    if not u or not check_password_hash(u['password'],str(data.get('password',''))):attempts[ip].append(time.time());return fail('RUN/correo o clave de demostración incorrectos.',401)
    if access=='staff' and u['role']=='citizen' or access=='citizen' and u['role']!='citizen':return fail('Esta cuenta debe ingresar desde el acceso correspondiente.',403)
    session.clear();session['uid']=u['id'];session['csrf']=secrets.token_urlsafe(32);session.permanent=True
    return jsonify(user=actor(),csrf=session['csrf'])

@app.post('/api/logout')
def logout():session.clear();return jsonify(ok=True)

@app.get('/api/requests')
@auth()
def requests_list():
    sql='SELECT r.*,u.name as owner_name FROM requests r JOIN users u ON u.id=r.user_id'
    vals=[]
    if g.user['role']=='citizen':sql+=' WHERE r.user_id=?';vals.append(g.user['id'])
    items=rows(sql+' ORDER BY r.created DESC, r.id DESC',vals)
    for item in items:
        item.update(document_overview(item))
        if g.user['role']=='citizen':item['ai']=None
    return jsonify(items=items)

@app.post('/api/requests')
@auth()
def create_request():
    d=request.get_json(silent=True) or {};typ=d.get('type_id');desc=str(d.get('description','')).strip()
    if typ not in {t['id'] for t in CATALOG} or len(desc)<15 or len(desc)>5000:return fail('Selecciona un trámite y describe tu solicitud (15 a 5.000 caracteres).')
    if g.user['role']!='citizen':return fail('Las solicitudes ciudadanas se ingresan con una cuenta de ciudadano.',403)
    duplicate=one("SELECT id,folio FROM requests WHERE user_id=? AND type_id=? AND status NOT IN ('Resuelta','Cerrada','Rechazada')",(g.user['id'],typ))
    if duplicate and not next(c for c in CATALOG if c['id']==typ)['allow_multiple_active']:return fail(f"Ya tienes una solicitud activa de este tipo: {duplicate['folio']}. Revisa su detalle antes de ingresar otra.",409)
    cur=db().execute('INSERT INTO requests(user_id,type_id,status,description,details,created,updated) VALUES(?,?,?,?,?,?,?)',(g.user['id'],typ,'Recibida',desc,dumps(d.get('details',{})),now(),now()));rid=cur.lastrowid
    folio=f'SOL-{datetime.now().year}-{rid:04}';db().execute('UPDATE requests SET folio=? WHERE id=?',(folio,rid));event(rid,'Recibida','Solicitud recibida. Puedes seguir su estado desde este portal.')
    notify(g.user['id'],'Solicitud recibida',f'Tu folio es {folio}.',f'/solicitudes/{rid}')
    return jsonify(id=rid,folio=folio),201

@app.get('/api/requests/<int:rid>')
@auth()
def detail(rid):
    r=request_record(rid)
    if not r:return fail('Solicitud no encontrada.',404)
    r['assigned_name']=(one('SELECT name FROM users WHERE id=?',(r['assigned_to'],)) or {}).get('name')
    r['details']=json.loads(r['details'] or '{}');r['ai']=json.loads(r['ai']) if r['ai'] else None
    events=rows('SELECT * FROM events WHERE deleted_at IS NULL AND request_id=?'+(" AND visibility='public'" if g.user['role']=='citizen' else '')+' ORDER BY id DESC',(rid,))
    docs=rows('SELECT * FROM documents WHERE request_id=? ORDER BY id DESC',(rid,))
    if g.user['role']=='citizen':
        r['ai']=None
        for d in docs:d['ai_review']=None
    r.update(document_overview(r,docs))
    return jsonify(request=r,events=events,documents=docs,requirements=document_groups(r,docs),appointments=rows('SELECT * FROM appointments WHERE request_id=? ORDER BY date DESC',(rid,)))

@app.patch('/api/requests/<int:rid>')
@auth(staff=True)
def update_request(rid):
    r=request_record(rid)
    if not r:return fail('Solicitud no encontrada.',404)
    d=request.get_json(silent=True) or {};status=d.get('status',r['status']);note=str(d.get('note','')).strip()
    if status not in STATUSES:return fail('Estado no válido.')
    if status=='Requiere antecedentes' and len(note)<10:return fail('Explica qué antecedentes debe entregar el ciudadano (al menos 10 caracteres).')
    if not note:note='El funcionario registró la resolución.' if status=='Resuelta' else 'El funcionario actualizó el estado del expediente.'
    if len(note)>3000:return fail('La observación es demasiado extensa.')
    if r['status'] in ('Resuelta','Cerrada','Rechazada'):return fail('Utiliza Reabrir expediente e indica el motivo antes de modificar una decisión final.',409)
    if status=='Resuelta' and any(x['status']!='Aceptado' for x in document_groups(r)):return fail('Acepta todos los antecedentes requeridos antes de resolver favorablemente.',409)
    assigned=d.get('assigned_to',r['assigned_to'])
    if assigned and not one("SELECT id FROM users WHERE id=? AND role IN ('staff','admin') AND active=1",(assigned,)):return fail('Funcionario no válido.')
    db().execute('UPDATE requests SET status=?,updated=?,assigned_to=? WHERE id=?',(status,now(),assigned,rid));event(rid,status,note)
    notify(r['user_id'],'Actualización de solicitud',f"{r['folio']}: {status}.",f'/solicitudes/{rid}'+('?accion=adjuntar' if status=='Requiere antecedentes' else ''))
    return jsonify(ok=True)

def document_review_context(r):
    owner=one('SELECT name,demo_run FROM users WHERE id=?',(r['user_id'],))
    return {**owner,'folio':r['folio']}

def run_document_review(raw,mime,requirement,r,force=False):
    try:
        result=inspect_document(raw,mime,requirement,profile=document_review_context(r),today=now()[:10],force=force)
    except Exception:
        result={'decision':'manual','reason':'No se pudo completar la lectura. El funcionario revisará el archivo.','source':'Control de disponibilidad','rules_version':'academico-v2'}
    if result:result['created']=now()
    return result

@app.post('/api/requests/<int:rid>/documents')
@auth()
def upload(rid):
    r=request_record(rid)
    if not r:return fail('Solicitud no encontrada.',404)
    if r['status'] in ('Resuelta','Cerrada','Rechazada'):return fail('Este expediente no admite nuevos antecedentes.',409)
    d=request.get_json(silent=True) or {};name=Path(str(d.get('name','documento'))).name[:160]
    try:raw=base64.b64decode(d.get('content',''),validate=True)
    except Exception:return fail('No se pudo leer el archivo.')
    if not raw or len(raw)>5*1024*1024:return fail('El archivo debe tener entre 1 byte y 5 MB.')
    if raw.startswith(b'%PDF-'):mime='application/pdf';ext='.pdf'
    elif raw.startswith(b'\x89PNG\r\n\x1a\n'):mime='image/png';ext='.png'
    elif raw.startswith(b'\xff\xd8\xff'):mime='image/jpeg';ext='.jpg'
    else:return fail('Solo se admiten PDF, PNG o JPG válidos.')
    if len(rows('SELECT id FROM documents WHERE request_id=?',(rid,)))>=12:return fail('El expediente admite hasta 12 documentos.')
    requirement=str(d.get('requirement','')).strip()
    requirement=REQUIREMENT_ALIASES.get(requirement,requirement)
    origin=str(d.get('origin','portal'))
    origin_note=str(d.get('origin_note','')).strip()[:500]
    if g.user['role']!='citizen' and (origin not in ('email','presencial') or len(origin_note)<10):return fail('Selecciona correo o atención presencial e indica su procedencia (al menos 10 caracteres).')
    if g.user['role']=='citizen':origin='portal';origin_note=''
    groups=document_groups(r)
    allowed=[x['name'] for x in groups]
    if not requirement:requirement=next((x['name'] for x in groups if x['status']=='Falta documento'),next((x['name'] for x in groups if x['status']=='Rechazado'),'Otros antecedentes'))
    if requirement not in allowed and requirement!='Otros antecedentes':return fail('Tipo de antecedente no válido.')
    current=one('SELECT * FROM documents WHERE request_id=? AND requirement=? AND superseded=0 ORDER BY id DESC',(rid,requirement))
    if current and current['review_status']=='Aceptado' and g.user['role']=='citizen':return fail('Este antecedente ya está aceptado; no requiere reemplazo.',409)
    path=secrets.token_hex(20)+ext;put_document(DATA,path,raw,mime)
    db().execute('UPDATE documents SET superseded=1 WHERE request_id=? AND requirement=? AND superseded=0',(rid,requirement))
    cur=db().execute('INSERT INTO documents(request_id,name,path,mime,size,created,requirement,origin,origin_note) VALUES(?,?,?,?,?,?,?,?,?)',(rid,name,path,mime,len(raw),now(),requirement,origin,origin_note))
    event(rid,r['status'],f'Antecedente incorporado: {name}.')
    if document_ai_enabled():
        result=run_document_review(raw,mime,requirement,r)
        if result:
            result['created']=now()
            db().execute('UPDATE documents SET ai_review=? WHERE id=?',(dumps(result),cur.lastrowid))
            title={'aceptar':'IA propone aceptar','observar':'IA propone observar','manual':'IA solicita revisión del funcionario'}[result['decision']]
            event(rid,title,requirement+': '+result['reason'],'internal')
    db().execute('UPDATE requests SET updated=? WHERE id=?',(now(),rid))
    return jsonify(id=cur.lastrowid),201

@app.post('/api/requests/<int:rid>/resubmit')
@auth()
def resubmit(rid):
    r=request_record(rid)
    if not r:return fail('Solicitud no encontrada.',404)
    if g.user['role']!='citizen' or r['status']!='Requiere antecedentes':return fail('Esta solicitud no requiere un reenvío de antecedentes.',409)
    last=one("SELECT id FROM events WHERE request_id=? AND status='Requiere antecedentes' AND note NOT LIKE 'Antecedente incorporado:%' ORDER BY id DESC LIMIT 1",(rid,))
    if not one("SELECT id FROM events WHERE request_id=? AND id>? AND note LIKE 'Antecedente incorporado:%'",(rid,last['id'] if last else 0)):return fail('Adjunta al menos un documento nuevo antes de enviar.')
    if document_overview(r)['document_tone']=='attention':return fail('Completa los documentos pendientes u observados antes de enviarlos a revisión.')
    db().execute("UPDATE requests SET status='En revisión',updated=? WHERE id=?",(now(),rid));event(rid,'En revisión','El ciudadano envió los antecedentes complementarios.');return jsonify(ok=True)

@app.get('/api/documents/<int:did>')
@auth()
def download(did):
    doc=one('SELECT * FROM documents WHERE id=?',(did,))
    if not doc or not request_record(doc['request_id']):return fail('Documento no encontrado.',404)
    return send_file(get_document(DATA,doc['path']),mimetype=doc['mime'],download_name=doc['name'],as_attachment=request.args.get('download')=='1')

@app.get('/api/requests/<int:rid>/receipt')
@auth()
def receipt(rid):
    r=request_record(rid)
    if not r:return fail('Solicitud no encontrada.',404)
    return send_file(io.BytesIO(simple_pdf('COMPROBANTE DE DEMOSTRACION',[r['folio'],r['owner_name'],f"Estado: {r['status']}",f"Fecha: {r['created'][:10]}",'Prototipo academico. Sin validez institucional.'])),mimetype='application/pdf',download_name=r['folio']+'.pdf',as_attachment=True)

@app.get('/api/appointments')
@auth()
def appointments():
    sql="SELECT a.*,COALESCE(u.name,'Visitante sin cita') as owner_name,r.folio,v.ticket,v.entered,v.started,v.exited FROM appointments a LEFT JOIN users u ON u.id=a.user_id LEFT JOIN requests r ON r.id=a.request_id LEFT JOIN visits v ON v.appointment_id=a.id"
    return jsonify(items=rows(sql+(' WHERE a.user_id=?' if g.user['role']=='citizen' else '')+' ORDER BY a.date,a.time', (g.user['id'],) if g.user['role']=='citizen' else ()))

@app.post('/api/appointments')
@auth(staff=True)
def schedule():
    d=request.get_json(silent=True) or {};rid=d.get('request_id');r=request_record(rid)
    if not r:return fail('Selecciona un expediente válido.')
    if r['status'] in ('Resuelta','Cerrada','Rechazada'):return fail('No se puede agendar un expediente cerrado.',409)
    date=str(d.get('date',''));tm=str(d.get('time',''))
    try:dt=datetime.strptime(date+' '+tm,'%Y-%m-%d %H:%M')
    except ValueError:return fail('Fecha u hora inválida.')
    if dt.date()<datetime.now(ZoneInfo('America/Santiago')).date():return fail('No puedes agendar una fecha pasada.')
    if tm not in ['09:00','09:30','10:00','10:30','11:00','11:30','12:00','12:30','14:00','14:30','15:00','15:30']:return fail('Elige un horario de atención disponible.')
    if one("SELECT id FROM appointments WHERE request_id=? AND status NOT IN ('Cancelada','Finalizada')",(rid,)):return fail('Este expediente ya tiene una cita vigente.',409)
    if one("SELECT id FROM appointments WHERE date=? AND time=? AND status NOT IN ('Cancelada','Finalizada')",(date,tm)):return fail('Ese horario ya está reservado. Selecciona otro.',409)
    code='CITA-'+secrets.token_hex(3).upper()
    cur=db().execute('INSERT INTO appointments(request_id,user_id,date,time,office,status,code,reason) VALUES(?,?,?,?,?,?,?,?)',(rid,r['user_id'],date,tm,OFFICE,'Pendiente de confirmación',code,str(d.get('reason','Revisión de antecedentes'))[:500]))
    db().execute("UPDATE requests SET status='Cita programada',appointment_requested=0,updated=? WHERE id=?",(now(),rid));event(rid,'Cita programada',f'Atención presencial agendada para {date} a las {tm}.')
    notify(r['user_id'],'Nueva cita programada','Confirma tu asistencia en Mis citas.',f'/citas?cita={cur.lastrowid}')
    return jsonify(ok=True,code=code),201

@app.patch('/api/appointments/<int:aid>')
@auth()
def appointment_action(aid):
    a=one('SELECT * FROM appointments WHERE id=?',(aid,));d=request.get_json(silent=True) or {};action=d.get('action')
    if action in ('start','finish'):return app.view_functions['attention'](aid)
    if not a or (g.user['role']=='citizen' and a['user_id']!=g.user['id']):return fail('Cita no encontrada.',404)
    if action=='confirm' and a['status']=='Pendiente de confirmación':status='Confirmada'
    elif action=='cancel' and a['status'] in ('Pendiente de confirmación','Confirmada'):
        status='Cancelada'
        r=one('SELECT status FROM requests WHERE id=?',(a['request_id'],))
        if r and r['status']=='Cita programada':db().execute("UPDATE requests SET status='En revisión',updated=? WHERE id=?",(now(),a['request_id']))
    elif action=='start' and g.user['role'] in ('staff','admin') and a['status']=='Presente':
        status='En atención';db().execute('UPDATE visits SET started=? WHERE appointment_id=?',(now(),aid))
    elif action=='finish' and g.user['role'] in ('staff','admin') and a['status']=='En atención':
        status='Finalizada';db().execute('UPDATE visits SET finished=? WHERE appointment_id=?',(now(),aid))
    else:return fail('La acción no está disponible para el estado actual.',409)
    db().execute('UPDATE appointments SET status=? WHERE id=?',(status,aid))
    if a['request_id']:event(a['request_id'],one('SELECT status FROM requests WHERE id=?',(a['request_id'],))['status'],f'Cita: {status}.')
    return jsonify(ok=True)

@app.post('/api/kiosk')
def kiosk():
    d=request.get_json(silent=True) or {};code=str(d.get('code','')).strip().upper();action=d.get('action','lookup')
    a=one('SELECT a.*,u.name as owner_name FROM appointments a JOIN users u ON u.id=a.user_id WHERE a.code=?',(code,))
    if not a:return fail('Código no encontrado. Revisa tu comprobante de cita.',404)
    v=one('SELECT * FROM visits WHERE appointment_id=?',(a['id'],))
    if action=='arrival':
        if a['date']!=str(datetime.now(ZoneInfo('America/Santiago')).date()):return fail('La llegada solo puede registrarse el día de la cita. Usa CITA-1002 para probar una cita de hoy.',409)
        if a['status']!='Confirmada':return fail('La cita debe estar confirmada y sin ingreso previo.',409)
        ticket=f"A-{a['id']:03}";db().execute('INSERT INTO visits(appointment_id,ticket,entered) VALUES(?,?,?)',(a['id'],ticket,now()));db().execute("UPDATE appointments SET status='Presente' WHERE id=?",(a['id'],))
        a['status']='Presente';v={'ticket':ticket,'entered':now(),'exited':None}
    elif action=='exit':
        if not v or v.get('exited'):return fail('No hay una visita abierta para este código.',409)
        if a['status']!='Finalizada':return fail('Tu atención todavía no ha finalizado. Consulta al funcionario antes de registrar la salida.',409)
        db().execute('UPDATE visits SET exited=? WHERE appointment_id=?',(now(),a['id']));db().execute("UPDATE appointments SET status='Finalizada' WHERE id=?",(a['id'],));a['status']='Finalizada';v['exited']=now()
    elif action!='lookup':return fail('Acción inválida.')
    return jsonify(appointment={k:a[k] for k in ('date','time','office','status','owner_name')},visit=v)

@app.get('/api/notifications')
@auth()
def notifications():return jsonify(items=active_notices(g.user['id']))

@app.patch('/api/notifications/<int:nid>')
@auth()
def notification_read(nid):db().execute('UPDATE notifications SET read=1 WHERE id=? AND user_id=?',(nid,g.user['id']));return jsonify(ok=True)

@app.get('/api/institutional')
@auth(staff=True)
def institutional_list():return jsonify(items=rows('SELECT i.*,u.name FROM institutional i JOIN users u ON u.id=i.user_id'),log=rows('SELECT * FROM query_log ORDER BY id DESC LIMIT 15'))

@app.post('/api/institutional/query')
@auth(staff=True)
def institutional_query():
    d=request.get_json(silent=True) or {};code=str(d.get('code','')).strip().upper();source=d.get('source')
    if source not in ('GEPOL','Registro Civil'):return fail('Origen de consulta inválido.')
    r=one('SELECT i.*,u.name FROM institutional i JOIN users u ON u.id=i.user_id WHERE person_code=?',(code,))
    result={'found':bool(r),'source':source,'simulated':True,'record':r}
    db().execute('INSERT INTO query_log(user_id,person_code,source,result,created) VALUES(?,?,?,?,?)',(g.user['id'],code,source,'Encontrado' if r else 'No encontrado',now()))
    return jsonify(result)

@app.post('/api/requests/<int:rid>/ai')
@auth(staff=True)
def analyze(rid):
    r=request_record(rid)
    if not r:return fail('Solicitud no encontrada.',404)
    if not document_ai_configured():return fail('Foundry aún no está configurado.',503)
    docs=rows('SELECT * FROM documents WHERE request_id=? AND superseded=0 ORDER BY id',(rid,))
    if not docs:return fail('Adjunta un documento para analizar su contenido.',400)
    # Límite explícito para no sobrepasar el tiempo de una petición ni multiplicar llamadas.
    selected=[d for d in docs if not d.get('ai_review') or json.loads(d['ai_review']).get('rules_version')!='academico-v2'][:3]
    if not selected:selected=docs[:3]
    results=[]
    for doc in selected:
        stored=get_document(DATA,doc['path'])
        raw=stored.read_bytes() if isinstance(stored,Path) else stored.read()
        result=run_document_review(raw,doc['mime'],doc['requirement'],r,force=True)
        db().execute('UPDATE documents SET ai_review=? WHERE id=?',(dumps(result),doc['id']))
        results.append((doc,result))
    labels={'aceptar':'Propone aceptar','observar':'Propone rechazar','manual':'Requiere revisión manual'}
    all_results=rows('SELECT requirement,ai_review FROM documents WHERE request_id=? AND superseded=0 ORDER BY id',(rid,))
    observations=[]
    for doc in all_results:
        proposal=json.loads(doc['ai_review']) if doc['ai_review'] else None
        observations.append(doc['requirement']+': '+(labels[proposal['decision']]+'. '+proposal['reason'] if proposal else 'Pendiente de análisis.'))
    result={'clasificacion':'Recomendaciones por documento · pendientes de confirmación humana','resumen':f'Se leyó el contenido de {len(results)} archivo(s) en esta ejecución. Consulta los criterios y coincidencias de cada documento. Máximo tres archivos por ejecución.','observaciones':observations,'borrador':'El funcionario debe confirmar la revisión de los documentos antes de comunicar una decisión al ciudadano.','created':now(),'source':'Microsoft Foundry','rules_version':'academico-v2'}
    db().execute('UPDATE requests SET ai=? WHERE id=?',(dumps(result),rid))
    event(rid,r['status'],'Se generaron recomendaciones sobre el contenido de los documentos; pendientes de confirmación humana.','internal')
    return jsonify(result)

@app.get('/api/admin')
@auth(admin=True)
def admin_info():return jsonify(users=rows('SELECT id,name,email,role,document,active FROM users ORDER BY id'),counts={t:one('SELECT COUNT(*) as total FROM '+t)['total'] for t in ['requests','documents','appointments','visits','query_log']},storage='Cloud SQL PostgreSQL + Cloud Storage privado' if os.environ.get('DB_HOST') else 'SQLite local + archivos locales',ai_configured=bool(os.environ.get('AZURE_OPENAI_ENDPOINT')))

@app.patch('/api/admin/users/<int:uid>')
@auth(admin=True)
def admin_user(uid):
    d=request.get_json(silent=True) or {}
    if uid==g.user['id']:return fail('No puedes desactivar tu propia cuenta.')
    if d.get('active') not in (0,1):return fail('Selecciona un estado válido.')
    db().execute('UPDATE users SET active=? WHERE id=?',(d['active'],uid));return jsonify(ok=True)

@app.get('/api/profile')
@auth()
def profile():return jsonify(user=g.user)

@app.patch('/api/profile')
@auth()
def update_profile():
    d=request.get_json(silent=True) or {};phone=str(d.get('phone','')).strip()[:40];address=str(d.get('address','')).strip()[:200]
    db().execute('UPDATE users SET phone=?,address=? WHERE id=?',(phone,address,g.user['id']));return jsonify(ok=True)

@app.get('/health')
def health():return jsonify(status='ok',mode='academic-demo')

@app.get('/')
@app.get('/<path:path>')
def frontend(path=''):
    if path.startswith('api/'):return fail('Recurso no encontrado.',404)
    return send_from_directory(ROOT/'static','index.html')

init()
from workflow import install, document_groups, document_overview, active_notices
install(globals())
from portal_v4 import install as install_v4
install_v4(globals())
from portal_v5 import install as install_v5
install_v5(globals())
from portal_v6 import install as install_v6
install_v6(globals())
from portal_v7 import install as install_v7
install_v7(globals())
if __name__=='__main__':app.run(host=os.environ.get('HOST','127.0.0.1'),port=int(os.environ.get('PORT','8080')),debug=False)
