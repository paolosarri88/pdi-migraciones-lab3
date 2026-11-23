"""Regresiones para revisión por documento, avisos resueltos y calendario."""
import base64
import unittest
import test_portal as base
portal=base.portal

class WorkflowTests(unittest.TestCase):
    login=base.PortalTests.login

    def test_10_run_alias(self):
        c,h=self.login('00.000.001-9','Ciudadano2026!')
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
