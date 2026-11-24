"""Recepción: permisos, exclusividad y capturas privadas, con base aislada."""
import base64
import unittest
import test_portal as base
portal=base.portal

class ReceptionTests(unittest.TestCase):
    login=base.PortalTests.login

    def test_25_attention_exclusive_and_owned(self):
        staff,h=self.login('funcionario@demo.pdi.cl','Funcionario2026!');admin,ha=self.login('admin@demo.pdi.cl','Admin2026!')
        # Two independent arrivals, deliberately start the later one first.
        a=staff.post('/api/people/7/arrivals',json={},headers=h);b=staff.post('/api/people/8/arrivals',json={},headers=h)
        self.assertEqual(a.status_code,201);self.assertEqual(b.status_code,201)
        aid,bid=a.json['id'],b.json['id']
        self.assertEqual(staff.patch(f'/api/appointments/{bid}/attention',json={'action':'start'},headers=h).status_code,200)
        self.assertEqual(staff.patch(f'/api/appointments/{aid}/attention',json={'action':'start'},headers=h).status_code,409)
        self.assertEqual(admin.patch(f'/api/appointments/{bid}/attention',json={'action':'start'},headers=ha).status_code,409)
        self.assertEqual(admin.patch(f'/api/appointments/{bid}/attention',json={'action':'finish'},headers=ha).status_code,409)
        self.assertEqual(staff.get('/api/workload').json['active']['id'],bid)
        self.assertEqual(staff.patch(f'/api/appointments/{bid}/attention',json={'action':'finish'},headers=h).status_code,200)
        self.assertEqual(staff.patch(f'/api/appointments/{aid}/attention',json={'action':'start'},headers=h).status_code,200)
        self.assertEqual(staff.patch(f'/api/appointments/{aid}/attention',json={'action':'finish'},headers=h).status_code,200)

    def test_26_reception_grant_and_private_files(self):
        kiosk=portal.app.test_client();hk={'X-CSRF-Token':kiosk.get('/api/bootstrap').json['csrf']}
        self.assertEqual(kiosk.post('/api/reception/complete',json={},headers=hk).status_code,403)
        self.assertEqual(kiosk.post('/api/reception/identify',json={'identifier':'000.000.01-9'},headers=hk).status_code,400)
        identified=kiosk.post('/api/reception/identify',json={'identifier':'00000001-9'},headers=hk)
        self.assertEqual(identified.status_code,200);token=identified.json['token']
        raw=base64.b64encode(portal.simple_pdf('ID',['Identidad ficticia para prueba.'])).decode()
        image=base64.b64encode(b'\xff\xd8\xff'+b'fixture').decode()
        payload={'token':token,'identification':raw,'face':image,'name':'identidad.pdf'}
        done=kiosk.post('/api/reception/complete',json=payload,headers=hk);self.assertEqual(done.status_code,201)
        self.assertEqual(kiosk.post('/api/reception/complete',json=payload,headers=hk).status_code,403)
        self.assertTrue(kiosk.post('/api/reception/identify',json={'identifier':'00000001-9'},headers=hk).json['registered'])
        staff,h=self.login('funcionario@demo.pdi.cl','Funcionario2026!');citizen,hc=self.login()
        reception=staff.get('/api/people/1/reception').json;cid=reception['capture']['id']
        self.assertEqual(citizen.get(f'/api/reception/captures/{cid}/face').status_code,403)
        self.assertEqual(kiosk.get(f'/api/reception/captures/{cid}/identification').status_code,401)
        downloaded=staff.get(f'/api/reception/captures/{cid}/identification');self.assertEqual(downloaded.status_code,200);self.assertTrue(downloaded.data.startswith(b'%PDF'));downloaded.close()
        newcase=staff.post('/api/people/1/requests',json={'type_id':'domicilio','description':'Solicitud presencial para revisar la identificación capturada.'},headers=h).json['id']
        attached=staff.post(f'/api/requests/{newcase}/reception-document',json={'capture_id':cid},headers=h)
        self.assertEqual(attached.status_code,201)
        version=next(x for x in staff.get(f'/api/requests/{newcase}').json['documents'] if x['id']==attached.json['id'])
        self.assertEqual(version['review_status'],'En revisión');self.assertEqual(version['origin'],'presencial')
        self.assertEqual(citizen.post(f'/api/requests/{newcase}/reception-document',json={'capture_id':cid},headers=hc).status_code,403)
        aid=reception['attention']['id'];staff.patch(f'/api/appointments/{aid}/attention',json={'action':'start'},headers=h)
        board=kiosk.get('/api/reception/board').json['items'];self.assertTrue(any(x['ticket']==done.json['ticket'] for x in board))
        self.assertFalse(any('demo_run' in x or 'email' in x for x in board))
        staff.patch(f'/api/appointments/{aid}/attention',json={'action':'finish'},headers=h)

    def test_27_history_edit_delete_and_closed_guard(self):
        staff,h=self.login('funcionario@demo.pdi.cl','Funcionario2026!');citizen,hc=self.login()
        rid=citizen.post('/api/requests',json={'type_id':'domicilio','description':'Caso aislado para corregir una decisión equivocada.'},headers=hc).json['id']
        staff.patch(f'/api/requests/{rid}',json={'status':'Rechazada','note':'Decisión equivocada durante la prueba.'},headers=h)
        original=staff.get(f'/api/requests/{rid}').json['events'][0];eid=original['id']
        payload={'status':'Requiere antecedentes','note':'Falta documento de domicilio legible.','reason':'Se eligió rechazo por error en el selector.','request_status':'Requiere antecedentes'}
        self.assertEqual(citizen.patch(f'/api/events/{eid}',json=payload,headers=hc).status_code,403)
        self.assertEqual(staff.patch(f'/api/events/{eid}',json=payload,headers=h).status_code,200)
        detail=staff.get(f'/api/requests/{rid}').json;self.assertEqual(detail['request']['status'],'Requiere antecedentes')
        self.assertEqual(staff.delete(f'/api/events/{eid}',json={'reason':'Anotación duplicada durante la prueba de corrección.'},headers=h).status_code,200)
        self.assertFalse(any(e['id']==eid for e in staff.get(f'/api/requests/{rid}').json['events']))
        with portal.app.app_context():
            edits=portal.rows('SELECT * FROM event_edits WHERE event_id=?',(eid,));self.assertEqual(len(edits),2);self.assertEqual(edits[0]['old_status'],'Rechazada')
        staff.patch(f'/api/requests/{rid}',json={'status':'Cerrada','note':'Cierre de expediente para controlar reapertura.'},headers=h)
        remaining=staff.get(f'/api/requests/{rid}').json['events'][0]['id']
        self.assertEqual(staff.patch(f'/api/events/{remaining}',json=payload,headers=h).status_code,409)
