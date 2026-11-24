"""Análisis aislado por archivo y avisos de documentos pendientes."""
import base64
import os
import unittest
from unittest.mock import patch
import test_portal as base
portal=base.portal

class DocumentActionsTests(unittest.TestCase):
    login=base.PortalTests.login
    def case(self):
        c,h=self.login();s,hs=self.login('funcionario@demo.pdi.cl','Funcionario2026!')
        r=c.post('/api/requests',json={'type_id':'domicilio','description':'Prueba de análisis individual y aviso de documento faltante.'},headers=h)
        self.assertEqual(r.status_code,201)
        return c,h,s,hs,r.json['id']
    def upload(self,c,h,rid,requirement):
        raw=base64.b64encode(portal.simple_pdf('ARCHIVO',['Documento simulado para una prueba aislada.'])).decode()
        r=c.post(f'/api/requests/{rid}/documents',json={'name':'prueba.pdf','content':raw,'requirement':requirement},headers=h)
        self.assertEqual(r.status_code,201);return r.json['id']
    def test_analysis_only_changes_selected_proposal(self):
        c,h,s,hs,rid=self.case();d1=self.upload(c,h,rid,'Documento de identidad');d2=self.upload(c,h,rid,'Antecedente de domicilio')
        before=s.get(f'/api/requests/{rid}').json
        result={'decision':'observar','reason':'Faltan campos mínimos de identificación.','source':'Microsoft Foundry','rules_version':'academico-v2'}
        with patch.object(portal,'document_ai_configured',return_value=True),patch.object(portal,'inspect_document',return_value=result) as inspect:
            response=s.post(f'/api/documents/{d1}/ai',json={},headers=hs)
        self.assertEqual(response.status_code,200);inspect.assert_called_once();self.assertTrue(inspect.call_args.kwargs['force'])
        after=s.get(f'/api/requests/{rid}').json;docs={d['id']:d for d in after['documents']}
        self.assertIn('observar',docs[d1]['ai_review']);self.assertIsNone(docs[d2]['ai_review'])
        self.assertEqual(docs[d1]['review_status'],'En revisión');self.assertIsNone(docs[d1]['reviewed_by'])
        self.assertEqual(before['request']['status'],after['request']['status'])
        self.assertEqual(c.post(f'/api/documents/{d1}/ai',json={},headers=h).status_code,403)
        self.upload(c,h,rid,'Documento de identidad')
        self.assertEqual(s.post(f'/api/documents/{d1}/ai',json={},headers=hs).status_code,409)
    def test_missing_document_notice_is_real_portal_only_and_deduplicated(self):
        c,h,s,hs,rid=self.case();url=f'/api/requests/{rid}/notify-document';body={'requirement':'Documento de identidad'}
        first=s.post(url,json=body,headers=hs);self.assertEqual(first.status_code,200)
        self.assertEqual(first.json['portal'],'registrado');self.assertFalse(first.json['duplicate'])
        self.assertEqual(first.json['channels'],{'email':'pending_configuration','whatsapp':'pending_configuration'})
        again=s.post(url,json=body,headers=hs);self.assertTrue(again.json['duplicate']);self.assertEqual(first.json['notification_id'],again.json['notification_id'])
        notices=c.get('/api/notifications').json['items'];self.assertTrue(any(n['id']==first.json['notification_id'] for n in notices))
        self.assertEqual(c.post(url,json=body,headers=h).status_code,403)
        self.assertEqual(s.post(url,json={'requirement':'No existe'},headers=hs).status_code,404)
        self.upload(c,h,rid,'Documento de identidad')
        self.assertEqual(s.post(url,json=body,headers=hs).status_code,409)
