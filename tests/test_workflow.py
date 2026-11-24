"""Regresiones para revisión por documento, avisos resueltos y calendario."""
import base64
import unittest
import test_portal as base
portal=base.portal

class WorkflowTests(unittest.TestCase):
    login=base.PortalTests.login

    def test_10_run_alias(self):
        c,h=self.login('00000001-9','Ciudadano2026!')
        self.assertEqual(c.get('/api/profile').json['user']['id'],1)

    def test_11_document_lifecycle_and_action_notices(self):
        citizen,h=self.login();staff,hs=self.login('funcionario@demo.pdi.cl','Funcionario2026!')
        r=citizen.post('/api/requests',json={'type_id':'vigencia-regiones','description':'Prueba de revisión individual de antecedentes ficticios.'},headers=h)
        self.assertEqual(r.status_code,201);rid=r.json['id']
        groups=citizen.get(f'/api/requests/{rid}').json['requirements']
        self.assertEqual(len(groups),2)
        raw=base64.b64encode(portal.simple_pdf('PRUEBA',['Antecedentes ficticios.'])).decode()
        def upload(name):return citizen.post(f'/api/requests/{rid}/documents',json={'name':'ejemplo.pdf','content':raw,'requirement':name},headers=h)
        first=upload(groups[0]['name']);self.assertEqual(first.status_code,201)
        self.assertEqual(citizen.patch(f"/api/documents/{first.json['id']}/review",json={'status':'Aceptado'},headers=h).status_code,403)
        self.assertEqual(staff.patch(f"/api/documents/{first.json['id']}/review",json={'status':'Aceptado'},headers=hs).status_code,200)
        self.assertEqual(citizen.get(f'/api/requests/{rid}').json['request']['display_status'],'Requiere antecedentes')
        self.assertEqual(upload(groups[0]['name']).status_code,409)
        second=upload(groups[1]['name']);did=second.json['id']
        self.assertEqual(staff.patch(f'/api/documents/{did}/review',json={'status':'Rechazado','note':'No se distingue el antecedente; adjunta una copia legible.'},headers=hs).status_code,200)
        self.assertTrue(any(n['target'].startswith(f'/solicitudes/{rid}?accion=adjuntar') for n in citizen.get('/api/notifications').json['items']))
        self.assertEqual(citizen.post(f'/api/requests/{rid}/resubmit',json={},headers=h).status_code,400)
        replacement=upload(groups[1]['name']);self.assertEqual(replacement.status_code,201)
        self.assertEqual(citizen.post(f'/api/requests/{rid}/resubmit',json={},headers=h).status_code,200)
        detail=citizen.get(f'/api/requests/{rid}').json
        self.assertEqual(detail['request']['display_status'],'En revisión')
        self.assertTrue(any(d['id']==did and d['superseded'] for d in detail['documents']))
        self.assertTrue(any(e['kind']=='document-rejected' for e in detail['events']))
        self.assertFalse(any(n['target'].startswith(f'/solicitudes/{rid}?accion=adjuntar') for n in citizen.get('/api/notifications').json['items']))
        self.assertEqual(staff.patch(f'/api/requests/{rid}',json={'status':'Resuelta','note':'Revisión final de prueba.'},headers=hs).status_code,409)
        self.assertEqual(staff.patch(f"/api/documents/{replacement.json['id']}/review",json={'status':'Aceptado'},headers=hs).status_code,200)
        self.assertEqual(staff.patch(f'/api/requests/{rid}',json={'status':'Resuelta','note':'Revisión final de prueba.'},headers=hs).status_code,200)

    def test_12_calendar_preferences_authorization(self):
        c,h=self.login()
        self.assertEqual(c.patch('/api/appointments/2/reminders',json={'minutes':[60]},headers=h).status_code,404)
        self.assertEqual(c.patch('/api/appointments/5/reminders',json={'minutes':[-1]},headers=h).status_code,400)
        r=c.patch('/api/appointments/5/reminders',json={'minutes':[5,60,1440],'phone':'+56 9 0000 0000'},headers=h)
        self.assertEqual(r.status_code,200);self.assertFalse(r.json['sms_enabled'])
        calendar=c.get('/api/appointments/5/calendar')
        self.assertEqual(calendar.status_code,200)
        self.assertEqual(calendar.mimetype,'text/calendar')
        self.assertEqual(calendar.data.count(b'BEGIN:VALARM'),3)
        self.assertIn(b'TRIGGER:-PT1440M',calendar.data)
        self.assertTrue(all(len(line)<=75 for line in calendar.data.split(b'\r\n')))
        self.assertEqual(c.get('/api/appointments/2/calendar').status_code,404)

    def test_13_completed_confirmation_notice_hidden(self):
        c,h=self.login()
        # The original tests canceled appointment 1; its old confirmation notice must be absent.
        self.assertFalse(any(n['target']=='/citas?cita=1' for n in c.get('/api/notifications').json['items']))

    def test_14_action_notices_follow_current_state_even_when_read(self):
        c,h=self.login()
        items=c.get('/api/notifications').json['items']
        pending=c.get('/api/requests').json['items']
        for r in pending:
            if r['display_status']=='Requiere antecedentes':
                self.assertTrue(any(n['target']==f"/solicitudes/{r['id']}?accion=adjuntar" and n.get('action_required') for n in items))
        with portal.app.app_context():
            portal.db().execute('UPDATE notifications SET read=1 WHERE user_id=1')
            portal.db().commit()
        after=c.get('/api/notifications').json['items']
        self.assertEqual({n['id'] for n in items if n.get('action_required')},{n['id'] for n in after if n.get('action_required')})

    def test_15_citizen_books_confirmed_slot_directly(self):
        from datetime import date,timedelta
        citizen,h=self.login();staff,hs=self.login('funcionario@demo.pdi.cl','Funcionario2026!')
        day=date.fromisoformat(citizen.get('/api/bootstrap').json['today'])+timedelta(days=1)
        while day.weekday()>4:day+=timedelta(days=1)
        available=citizen.get('/api/appointment-slots?date='+str(day)).json['slots'];self.assertTrue(available)
        booked=citizen.post('/api/appointments/book',json={'date':str(day),'time':available[0]},headers=h)
        self.assertEqual(booked.status_code,201);self.assertEqual(booked.json['status'],'Confirmada')
        self.assertRegex(booked.json['code'],r'^CITA-\d+$')
        self.assertNotIn(available[0],citizen.get('/api/appointment-slots?date='+str(day)).json['slots'])
        self.assertEqual(staff.post('/api/appointments',json={},headers=hs).status_code,410)
        other,ho=self.login('persona2@demo.pdi.cl','Ciudadano2026!')
        self.assertEqual(other.post('/api/appointments/book',json={'date':str(day),'time':available[0]},headers=ho).status_code,409)

    def test_16_document_examples_and_help(self):
        c=portal.app.test_client()
        help=c.get('/api/bootstrap').json['document_help']
        self.assertIn('cuenta ficticia',help['Antecedente de domicilio']['description'])
        self.assertNotEqual(help['Antecedente de domicilio']['key'],help['Antecedente de residencia']['key'])
        self.assertEqual(c.get('/api/document-examples/identidad').mimetype,'application/pdf')
        self.assertEqual(c.get('/api/document-examples/no-existe').status_code,404)

    def test_17_ai_guardrails_do_not_auto_accept_missing_fields(self):
        from document_ai import normalize_result
        from document_rules import DOCUMENT_RULES
        rule=DOCUMENT_RULES['identidad']
        result={'decision':'aceptar','confidence':0.99,'document_type_matches':True,'legible':True,'checks':[],'reason':'Prueba de resultado incompleto.'}
        self.assertEqual(normalize_result(result,rule)['decision'],'manual')
        result['checks']=[{'field':f,'present':True,'evidence':'Texto ficticio visible'} for f in rule['fields']]
        self.assertEqual(normalize_result(result,rule)['decision'],'aceptar')
        result['legible']=False
        self.assertEqual(normalize_result(result,rule)['decision'],'manual')
        result['confidence']='alta'
        self.assertRaises(ValueError,normalize_result,result,rule)

    def test_18_auto_document_result_is_audited_and_failure_keeps_manual_review(self):
        import os
        from unittest.mock import patch
        c,h=self.login()
        created=c.post('/api/requests',json={'type_id':'tarjeta-turismo','description':'Prueba aislada del flujo de prevalidación automática.'},headers=h)
        self.assertEqual(created.status_code,201);rid=created.json['id']
        raw=base64.b64encode(portal.simple_pdf('ARCHIVO DE PRUEBA',['Contenido ficticio.'])).decode()
        payload={'name':'ejemplo.pdf','content':raw,'requirement':'Documento de viaje de prueba'}
        config={'AUTO_DOCUMENT_REVIEW':'1','AZURE_OPENAI_ENDPOINT':'https://test.openai.azure.com','AZURE_OPENAI_API_KEY':'test-only','AZURE_OPENAI_DEPLOYMENT':'test-only'}
        result={'decision':'observar','reason':'El archivo ficticio no presenta un documento de viaje.','source':'Microsoft Foundry','rules_version':'academico-v1'}
        # Fake only the external transport boundary; this does not prove real Azure quality.
        with patch.dict(os.environ,config),patch.object(portal,'inspect_document',return_value=result):
            upload=c.post(f'/api/requests/{rid}/documents',json=payload,headers=h)
        self.assertEqual(upload.status_code,201)
        detail=c.get(f'/api/requests/{rid}').json
        self.assertEqual(detail['documents'][0]['review_status'],'En revisión')
        staff,hs=self.login('funcionario@demo.pdi.cl','Funcionario2026!')
        internal=staff.get(f'/api/requests/{rid}').json
        self.assertIn('academico-v1',internal['documents'][0]['ai_review'])
        self.assertTrue(any(e['status']=='IA propone observar' for e in internal['events']))
        self.assertFalse(any(e['status']=='IA propone observar' for e in detail['events']))
        self.assertEqual(staff.patch(f"/api/documents/{upload.json['id']}/review",json={'status':'Rechazado','note':'El archivo no corresponde a un documento de viaje.'},headers=hs).status_code,200)
        with patch.dict(os.environ,config),patch.object(portal,'inspect_document',side_effect=TimeoutError):
            replacement=c.post(f'/api/requests/{rid}/documents',json=payload,headers=h)
        self.assertEqual(replacement.status_code,201)
        detail=c.get(f'/api/requests/{rid}').json
        self.assertEqual(detail['documents'][0]['review_status'],'En revisión')
        self.assertIn('Control de disponibilidad',staff.get(f'/api/requests/{rid}').json['documents'][0]['ai_review'])

    def test_19_registration_access_and_run_format(self):
        c=portal.app.test_client();csrf=c.get('/api/bootstrap').json['csrf'];h={'X-CSRF-Token':csrf}
        created=c.post('/api/register',json={'name':'Persona Nueva','email':'nueva@example.test','password':'MiClaveNueva2026!','role':'admin'},headers=h)
        self.assertEqual(created.status_code,201);run=created.json['run']
        self.assertRegex(run,r'^\d{8}-[0-9K]$')
        for invalid in ('000000019','00.000.001-9'):
            self.assertEqual(c.post('/api/login',json={'email':invalid,'password':'Ciudadano2026!'},headers=h).status_code,400)
        self.assertEqual(c.post('/api/login',json={'email':run,'password':'MiClaveNueva2026!','access':'staff'},headers=h).status_code,400)
        good=c.post('/api/login',json={'email':run,'password':'MiClaveNueva2026!','access':'citizen'},headers=h)
        self.assertEqual(good.status_code,200);self.assertEqual(good.json['user']['role'],'citizen')
        self.assertEqual(c.get('/api/workboard').status_code,403)
        names=portal.app.test_client().get('/api/demo-accounts').json['items']
        self.assertFalse(any(a['email']=='nueva@example.test' for a in names))

    def test_20_repeatable_certificates_and_work_priorities(self):
        c,h=self.login()
        payload={'type_id':'viajes','description':'Certificado de otro período solicitado por la persona.'}
        self.assertEqual(c.post('/api/requests',json=payload,headers=h).status_code,201)
        self.assertEqual(c.post('/api/requests',json=payload,headers=h).status_code,201)
        staff,hs=self.login('funcionario@demo.pdi.cl','Funcionario2026!')
        board=staff.get('/api/workboard').json
        if board['queue']:self.assertEqual(board['queue'][0]['status'],'En atención')
        self.assertTrue(any(t['action'].startswith('Revisar') for t in board['tasks']))
        with portal.app.app_context():
            portal.db().execute("UPDATE requests SET type_id='orientacion',status='Cita programada' WHERE id=3")
            portal.db().execute("UPDATE documents SET review_status='Aceptado' WHERE request_id=3")
            portal.db().execute("UPDATE appointments SET status='Cancelada' WHERE request_id=3")
            portal.db().commit()
        updated=staff.get('/api/workboard').json
        self.assertEqual(next(t['action'] for t in updated['tasks'] if t['id']==3),'Resolver expediente')

    def test_21_institutional_windows_and_permissions(self):
        citizen,h=self.login();staff,hs=self.login('funcionario@demo.pdi.cl','Funcionario2026!')
        self.assertEqual(citizen.get('/api/institutional/people').status_code,403)
        self.assertEqual(citizen.post('/api/simulators/gepol/query',json={'run':'00000001-9'},headers=h).status_code,403)
        people=staff.get('/api/institutional/people').json['items']
        self.assertTrue(any(p['run']=='00000001-9' for p in people))
        geop=staff.post('/api/simulators/gepol/query',json={'run':'00000001-9'},headers=hs)
        civil=staff.post('/api/simulators/registro-civil/query',json={'name':'Michael De Santa'},headers=hs)
        self.assertEqual(geop.status_code,200);self.assertEqual(civil.status_code,200)
        self.assertIn('migration_status',geop.json['items'][0]);self.assertNotIn('migration_status',civil.json['items'][0])
        self.assertEqual(staff.post('/api/simulators/gepol/query',json={'run':'00.000.001-9'},headers=hs).status_code,400)
        self.assertEqual(staff.post('/api/simulators/desconocido/query',json={'run':'00000001-9'},headers=hs).status_code,404)
        self.assertEqual(staff.get('/simuladores/gepol').status_code,200)
        self.assertEqual(staff.get('/simuladores/registro-civil').status_code,200)
        self.assertIn(b'kiosk.js',staff.get('/totem').data)

    def test_22_staff_upload_requires_explicit_provenance(self):
        staff,h=self.login('funcionario@demo.pdi.cl','Funcionario2026!')
        raw=base64.b64encode(portal.simple_pdf('ARCHIVO',['Contenido ficticio.'])).decode()
        payload={'name':'correo.pdf','content':raw,'requirement':'Otros antecedentes'}
        self.assertEqual(staff.post('/api/requests/1/documents',json=payload,headers=h).status_code,400)
        payload.update(origin='email',origin_note='Recibido en el correo institucional del expediente.')
        result=staff.post('/api/requests/1/documents',json=payload,headers=h)
        self.assertEqual(result.status_code,201)
        docs=staff.get('/api/requests/1').json['documents']
        current=next(d for d in docs if d['id']==result.json['id'])
        self.assertEqual(current['origin'],'email');self.assertIn('correo institucional',current['origin_note'])

    def test_23_person_presential_additional_and_rectification(self):
        staff,h=self.login('funcionario@demo.pdi.cl','Funcionario2026!');citizen,hc=self.login()
        self.assertEqual(citizen.get('/api/people/1').status_code,403)
        made=staff.post('/api/people',json={'name':'Persona Presencial','email':'presencial-v5@example.test','password':'PruebaPresencial2026!','role':'admin','phone':'1234'},headers=h)
        self.assertEqual(made.status_code,201);uid=made.json['id']
        person=staff.get(f'/api/people/{uid}').json['person'];self.assertEqual(person['phone'],'1234')
        created=staff.post(f'/api/people/{uid}/requests',json={'type_id':'domicilio','description':'Atención presencial para registrar y revisar antecedentes.'},headers=h)
        self.assertEqual(created.status_code,201);rid=created.json['id']
        self.assertEqual(staff.get(f'/api/requests/{rid}').json['request']['channel'],'presencial')
        extra_name=next(n for c in portal.CATALOG for n in c['docs'] if n not in next(c['docs'] for c in portal.CATALOG if c['id']=='domicilio'))
        payload={'name':extra_name,'reason':'Se requiere este antecedente complementario para revisar el caso.'}
        self.assertEqual(citizen.post(f'/api/requests/{rid}/requirements',json=payload,headers=hc).status_code,403)
        extra=staff.post(f'/api/requests/{rid}/requirements',json=payload,headers=h);self.assertEqual(extra.status_code,201)
        self.assertEqual(staff.post(f'/api/requests/{rid}/requirements',json=payload,headers=h).status_code,409)
        self.assertIn(extra_name,[x['name'] for x in staff.get(f'/api/requests/{rid}').json['requirements']])
        self.assertEqual(staff.post(f'/api/requests/{rid}/requirements/{extra.json["id"]}/cancel',json={'reason':'Fue solicitado por error durante la revisión.'},headers=h).status_code,200)
        self.assertNotIn(extra_name,[x['name'] for x in staff.get(f'/api/requests/{rid}').json['requirements']])
        self.assertEqual(staff.patch(f'/api/requests/{rid}',json={'status':'Rechazada','note':'Decisión registrada durante una prueba controlada.'},headers=h).status_code,200)
        self.assertEqual(staff.patch(f'/api/requests/{rid}',json={'status':'En revisión','note':'Cambio normal no permitido.'},headers=h).status_code,409)
        self.assertEqual(staff.post(f'/api/requests/{rid}/reopen',json={'reason':'Se corrige la decisión de prueba y se retoma la revisión.'},headers=h).status_code,200)
        detail=staff.get(f'/api/requests/{rid}').json
        rejected=next(e for e in detail['events'] if e['status']=='Rechazada')
        self.assertEqual(staff.post(f'/api/events/{rejected["id"]}/rectify',json={'reason':'La anotación correspondía a una prueba y queda rectificada.'},headers=h).status_code,200)
        detail=staff.get(f'/api/requests/{rid}').json
        self.assertTrue(next(e for e in detail['events'] if e['id']==rejected['id'])['rectified_at'])
        self.assertEqual(detail['request']['status'],'En revisión')
        arrival=staff.post(f'/api/people/{uid}/arrivals',json={},headers=h);self.assertEqual(arrival.status_code,201)
        self.assertEqual(staff.post(f'/api/people/{uid}/arrivals',json={},headers=h).status_code,409)
        self.assertEqual(staff.patch(f'/api/appointments/{arrival.json["id"]}',json={'action':'start'},headers=h).status_code,200)
        self.assertEqual(staff.patch(f'/api/appointments/{arrival.json["id"]}',json={'action':'finish'},headers=h).status_code,200)

    def test_24_document_reuse_is_owned_versioned_and_pending(self):
        staff,h=self.login('funcionario@demo.pdi.cl','Funcionario2026!');citizen,hc=self.login()
        def case():return citizen.post('/api/requests',json={'type_id':'domicilio','description':'Nueva solicitud para probar referencias documentales.'},headers=hc).json['id']
        rid=case();target=case();name=citizen.get(f'/api/requests/{rid}').json['requirements'][0]['name']
        raw=base64.b64encode(portal.simple_pdf('DOCUMENTO',['Contenido ficticio para la prueba.'])).decode()
        upload=staff.post(f'/api/requests/{rid}/documents',json={'name':'copia.pdf','content':raw,'requirement':name,'origin':'presencial','origin_note':'Copia presentada y revisada durante la atención presencial.'},headers=h)
        self.assertEqual(upload.status_code,201);did=upload.json['id']
        self.assertEqual(citizen.post(f'/api/requests/{target}/reuse-document',json={'document_id':did,'requirement':name},headers=hc).status_code,409)
        self.assertEqual(staff.patch(f'/api/documents/{did}/review',json={'status':'Aceptado'},headers=h).status_code,200)
        reuse=citizen.post(f'/api/requests/{target}/reuse-document',json={'document_id':did,'requirement':name},headers=hc)
        self.assertEqual(reuse.status_code,201)
        copied=next(d for d in citizen.get(f'/api/requests/{target}').json['documents'] if d['id']==reuse.json['id'])
        self.assertEqual(copied['source_document_id'],did);self.assertEqual(copied['review_status'],'En revisión');self.assertIsNone(copied['reviewed_by'])
        other,ho=self.login('persona4@demo.pdi.cl','Ciudadano2026!')
        self.assertEqual(other.get('/api/people/1/documents').status_code,403)
        self.assertEqual(staff.patch(f'/api/documents/{did}/validity',json={'valid_until':'2020-01-01','reason':'Fecha de vencimiento informada en el documento.'},headers=h).status_code,200)
        newer=case()
        self.assertEqual(citizen.post(f'/api/requests/{newer}/reuse-document',json={'document_id':did,'requirement':name},headers=hc).status_code,409)
