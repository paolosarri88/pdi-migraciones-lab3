"""Regresiones de deshacer, reservas confirmadas y visitante provisional."""
import base64
import unittest
import test_portal as base
portal=base.portal

class NewFlows(unittest.TestCase):
    login=base.PortalTests.login

    def test_30_undo_restores_document_and_terminal_state(self):
        staff,h=self.login('funcionario@demo.pdi.cl','Funcionario2026!');citizen,hc=self.login()
        rid=staff.post('/api/people/1/requests',json={'type_id':'domicilio'},headers=h).json['id']
        groups=staff.get(f'/api/requests/{rid}').json['requirements']
        raw=base64.b64encode(portal.simple_pdf('ID',['Solo datos ficticios.'])).decode()
        did=staff.post(f'/api/requests/{rid}/documents',json={'name':'identidad.pdf','content':raw,'requirement':groups[0]['name'],'origin':'presencial','origin_note':'Recibido durante la atención y pendiente de comprobación.'},headers=h).json['id']
        staff.patch(f'/api/documents/{did}/review',json={'status':'Aceptado'},headers=h)
        detail=staff.get(f'/api/requests/{rid}').json;eid=detail['events'][0]['id']
        self.assertEqual(citizen.delete(f'/api/events/{eid}',json={'reason':'No había comprobado la vigencia del documento.'},headers=hc).status_code,403)
        self.assertEqual(staff.delete(f'/api/events/{eid}',json={'reason':'No había comprobado la vigencia del documento.'},headers=h).status_code,200)
        detail=staff.get(f'/api/requests/{rid}').json;self.assertEqual(next(d for d in detail['documents'] if d['id']==did)['review_status'],'En revisión')
        self.assertFalse(any(e['id']==eid for e in detail['events']))
        before=detail['request']['status']
        staff.patch(f'/api/requests/{rid}',json={'status':'Rechazada','note':'Rechazo accidental durante la prueba.'},headers=h)
        eid=staff.get(f'/api/requests/{rid}').json['events'][0]['id']
        self.assertEqual(staff.delete(f'/api/events/{eid}',json={'reason':'Se seleccionó rechazo en lugar de continuar revisando.'},headers=h).status_code,200)
        self.assertEqual(staff.get(f'/api/requests/{rid}').json['request']['status'],before)
        self.assertEqual(staff.get(f'/api/requests/{rid}/certificate').status_code,409)
        # Undo incorporation too: original file stays archived, not current.
        eid=staff.get(f'/api/requests/{rid}').json['events'][0]['id']
        self.assertEqual(staff.delete(f'/api/events/{eid}',json={'reason':'La copia incorporada no correspondía a esta solicitud.'},headers=h).status_code,200)
        self.assertTrue(next(d for d in staff.get(f'/api/requests/{rid}').json['documents'] if d['id']==did)['superseded'])

    def test_31_certificate_requires_all_active_requirements(self):
        staff,h=self.login('funcionario@demo.pdi.cl','Funcionario2026!')
        rid=staff.post('/api/people/1/requests',json={'type_id':'domicilio'},headers=h).json['id']
        self.assertEqual(staff.patch(f'/api/requests/{rid}',json={'status':'Resuelta'},headers=h).status_code,409)
        groups=staff.get(f'/api/requests/{rid}').json['requirements'];raw=base64.b64encode(portal.simple_pdf('ID',['Datos ficticios.'])).decode()
        for group in groups:
            did=staff.post(f'/api/requests/{rid}/documents',json={'name':'documento.pdf','content':raw,'requirement':group['name'],'origin':'presencial','origin_note':'Presentado y contrastado durante la atención presencial.'},headers=h).json['id']
            staff.patch(f'/api/documents/{did}/review',json={'status':'Aceptado'},headers=h)
        self.assertEqual(staff.patch(f'/api/requests/{rid}',json={'status':'Resuelta'},headers=h).status_code,200)
        citizen,hc=self.login();pdf=citizen.get(f'/api/requests/{rid}/certificate');self.assertEqual(pdf.status_code,200);self.assertTrue(pdf.data.startswith(b'%PDF'));pdf.close()
        self.assertEqual(staff.patch(f'/api/requests/{rid}',json={'status':'Requiere antecedentes'},headers=h).status_code,400)

    def test_32_walkin_receives_private_provisional_turn(self):
        kiosk=portal.app.test_client();h={'X-CSRF-Token':kiosk.get('/api/bootstrap').json['csrf']}
        token=kiosk.post('/api/reception/identify',json={'walk_in':True},headers=h).json['token']
        raw=base64.b64encode(portal.simple_pdf('COPIA',['Documento ficticio.'])).decode();face=base64.b64encode(b'\xff\xd8\xfffixture').decode()
        response=kiosk.post('/api/reception/complete',json={'token':token,'identification':raw,'face':face,'name':'identificacion.pdf'},headers=h)
        self.assertEqual(response.status_code,201)
        staff,hs=self.login('funcionario@demo.pdi.cl','Funcionario2026!')
        queue=staff.get('/api/workboard').json['queue'];guest=next(a for a in queue if a['ticket']==response.json['ticket']);self.assertIsNone(guest['user_id'])
        aid=guest['id'];self.assertEqual(kiosk.get(f'/api/receptions/{aid}').status_code,401)
        self.assertEqual(staff.patch(f'/api/appointments/{aid}/attention',json={'action':'start'},headers=hs).status_code,200)
        linked=staff.post(f'/api/receptions/{aid}/link-person',json={'user_id':1,'note':'Documento y fotografía contrastados con la persona presente.'},headers=hs)
        self.assertEqual(linked.status_code,200);self.assertEqual(staff.get(f'/api/receptions/{aid}').json['attention']['user_id'],1)
        self.assertEqual(staff.patch(f'/api/appointments/{aid}/attention',json={'action':'finish'},headers=hs).status_code,200)

    def test_33_expected_appointment_is_not_queue_until_arrival(self):
        from datetime import date,timedelta
        citizen,h=self.login();staff,hs=self.login('funcionario@demo.pdi.cl','Funcionario2026!')
        day=date.fromisoformat(citizen.get('/api/bootstrap').json['today'])+timedelta(days=8)
        while day.weekday()>4:day+=timedelta(days=1)
        slots=citizen.get('/api/appointment-slots?date='+str(day)).json['slots']
        booked=citizen.post('/api/appointments/book',json={'date':str(day),'time':slots[-1]},headers=h);self.assertEqual(booked.status_code,201)
        aid=booked.json['id'];self.assertFalse(any(a['id']==aid for a in staff.get('/api/workboard').json['queue']))
        expected=staff.get('/api/reception/day?date='+str(day)).json['items'];self.assertTrue(any(a['id']==aid and a['status']=='Confirmada' for a in expected))

    def test_34_duplicate_assignment_note_can_be_undone(self):
        staff,h=self.login('funcionario@demo.pdi.cl','Funcionario2026!')
        rid=staff.post('/api/people/1/requests',json={'type_id':'domicilio'},headers=h).json['id']
        for _ in range(2):self.assertEqual(staff.patch(f'/api/requests/{rid}/assignment',json={'take':True},headers=h).status_code,200)
        eid=staff.get(f'/api/requests/{rid}').json['events'][0]['id']
        self.assertEqual(staff.delete(f'/api/events/{eid}',json={'reason':'Asignación registrada dos veces por un doble clic.'},headers=h).status_code,200)
        self.assertEqual(staff.get(f'/api/requests/{rid}').json['request']['assigned_to'],2)
