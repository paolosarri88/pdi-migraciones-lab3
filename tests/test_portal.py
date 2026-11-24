"""Pruebas de los flujos y límites de acceso; usan una base temporal aislada."""
import base64
import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

TMP=tempfile.TemporaryDirectory()
if os.environ.get('DB_HOST') and not os.environ.get('DB_NAME','').startswith('pdi_validation_'):
    raise RuntimeError('Las pruebas cloud requieren una base aislada con prefijo pdi_validation_.')
os.environ['PDI_DATA_DIR']=TMP.name
spec=importlib.util.spec_from_file_location('portal',Path(__file__).parents[1]/'app.py')
portal=importlib.util.module_from_spec(spec);spec.loader.exec_module(portal)
portal.app.config['TESTING']=True

class PortalTests(unittest.TestCase):
    def login(self,email='ciudadano@demo.pdi.cl',password='Ciudadano2026!'):
        c=portal.app.test_client();csrf=c.get('/api/bootstrap').json['csrf']
        r=c.post('/api/login',json={'email':email,'password':password},headers={'X-CSRF-Token':csrf})
        self.assertEqual(r.status_code,200)
        return c,{'X-CSRF-Token':r.json['csrf']}

    def test_01_auth_and_csrf(self):
        c=portal.app.test_client()
        self.assertEqual(c.get('/api/requests').status_code,401)
        self.assertEqual(c.post('/api/login',json={}).status_code,403)
        c,h=self.login()
        self.assertEqual(c.get('/api/admin').status_code,403)
        self.assertEqual(c.get('/api/institutional').status_code,403)
        self.assertEqual(c.post('/api/institutional/query',json={'code':'DEMO-002','source':'GEPOL'},headers=h).status_code,403)

    def test_02_owner_isolation_and_documents(self):
        c,h=self.login()
        self.assertEqual(len(c.get('/api/requests').json['items']),6)
        self.assertEqual(c.get('/api/requests/7').status_code,404)
        self.assertEqual(c.get('/api/documents/7').status_code,404)
        self.assertEqual(c.patch('/api/requests/1',json={'status':'Resuelta','note':'No permitido'},headers=h).status_code,403)
        self.assertEqual(c.get('/api/requests/1/receipt').mimetype,'application/pdf')
        self.assertEqual(c.get('/api/requests/1').json['request']['ai'],None)

    def test_03_create_duplicate_upload_resubmit(self):
        c,h=self.login()
        payload={'type_id':'duplicado-visa','description':'Solicitud ficticia para probar el recorrido completo.','details':{'Año del registro':'2026'}}
        r=c.post('/api/requests',json=payload,headers=h);self.assertEqual(r.status_code,201);rid=r.json['id']
        self.assertEqual(c.post('/api/requests',json=payload,headers=h).status_code,409)
        self.assertEqual(c.post(f'/api/requests/{rid}/documents',json={'name':'malicioso.html','content':base64.b64encode(b'<script>alert(1)</script>').decode()},headers=h).status_code,400)
        raw=portal.simple_pdf('PRUEBA',['Documento ficticio.'])
        self.assertEqual(c.post(f'/api/requests/{rid}/documents',json={'name':'prueba.pdf','content':base64.b64encode(raw).decode()},headers=h).status_code,201)
        staff,hs=self.login('funcionario@demo.pdi.cl','Funcionario2026!')
        self.assertEqual(staff.patch('/api/requests/2',json={'status':'Requiere antecedentes','note':'Adjunta un documento de prueba.'},headers=hs).status_code,200)
        self.assertEqual(c.post('/api/requests/2/resubmit',json={},headers=h).status_code,400)
        self.assertEqual(c.post('/api/requests/2/documents',json={'name':'nuevo.pdf','content':base64.b64encode(raw).decode()},headers=h).status_code,201)
        self.assertEqual(c.post('/api/requests/2/resubmit',json={},headers=h).status_code,200)
        self.assertEqual(c.get('/api/requests/2').json['request']['status'],'En revisión')

    def test_04_appointment_authorization_and_state(self):
        c,h=self.login()
        self.assertEqual(c.patch('/api/appointments/2',json={'action':'cancel'},headers=h).status_code,404)
        self.assertEqual(c.patch('/api/appointments/1',json={'action':'confirm'},headers=h).status_code,409)
        self.assertEqual(c.patch('/api/appointments/1',json={'action':'confirm'},headers=h).status_code,409)
        self.assertEqual(c.patch('/api/appointments/1',json={'action':'cancel'},headers=h).status_code,200)
        self.assertEqual(c.get('/api/requests/3').json['request']['status'],'En revisión')

    def test_05_kiosk_arrival_attention_exit(self):
        c=portal.app.test_client();h={'X-CSRF-Token':c.get('/api/bootstrap').json['csrf']}
        r=c.post('/api/kiosk',json={'code':'CITA-1002','action':'arrival'},headers=h)
        self.assertEqual(r.status_code,200);self.assertEqual(r.json['appointment']['status'],'Presente')
        self.assertNotIn('email',r.json['appointment'])
        self.assertEqual(c.post('/api/kiosk',json={'code':'CITA-1002','action':'arrival'},headers=h).status_code,409)
        staff,hs=self.login('funcionario@demo.pdi.cl','Funcionario2026!')
        self.assertEqual(staff.patch('/api/appointments/2',json={'action':'start'},headers=hs).status_code,200)
        self.assertEqual(staff.patch('/api/appointments/2',json={'action':'finish'},headers=hs).status_code,200)
        self.assertEqual(c.post('/api/kiosk',json={'code':'CITA-1002','action':'exit'},headers=h).status_code,200)
        self.assertEqual(c.post('/api/kiosk',json={'code':'CITA-1002','action':'exit'},headers=h).status_code,409)

    def test_06_admin_and_institutional(self):
        c,h=self.login('admin@demo.pdi.cl','Admin2026!')
        self.assertEqual(c.get('/api/admin').status_code,200)
        self.assertEqual(c.patch('/api/admin/users/3',json={'active':0},headers=h).status_code,400)
        self.assertEqual(c.patch('/api/admin/users/15',json={'active':0},headers=h).status_code,200)
        r=c.post('/api/institutional/query',json={'code':'DEMO-001','source':'GEPOL'},headers=h)
        self.assertEqual(r.status_code,200);self.assertTrue(r.json['simulated'])
        self.assertEqual(c.post('/api/institutional/query',json={'code':'DEMO-001','source':'Falso'},headers=h).status_code,400)
        # Sin configuración externa, no se inventa un resultado de IA.
        for k in ['AZURE_OPENAI_ENDPOINT','AZURE_OPENAI_API_KEY','AZURE_OPENAI_DEPLOYMENT']:os.environ.pop(k,None)
        self.assertEqual(c.post('/api/requests/1/ai',json={},headers=h).status_code,503)

if __name__=='__main__':unittest.main()
