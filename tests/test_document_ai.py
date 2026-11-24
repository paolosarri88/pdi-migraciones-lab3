"""Controles locales frente a respuestas del modelo contradictorias."""
import unittest
from document_ai import normalize_result
from document_rules import DOCUMENT_RULES, rule_key

class DocumentReviewTests(unittest.TestCase):
    def result(self):
        return {'decision':'aceptar','confidence':0.99,'legible':True,'document_type_matches':True,'reason':'Todos los campos visibles.', 'checks':[{'field':f,'present':True,'evidence':'Texto visible'} for f in DOCUMENT_RULES['identidad']['fields']], 'extracted':{'holder_name':'Niko Bellic','personal_id':'00000004-9','expiry_date':'2030-01-01'}}
    def check(self,r):
        return normalize_result(r,DOCUMENT_RULES['identidad'],{'name':'Niko Bellic','demo_run':'000000049'},'2026-11-24')
    def test_correct_simulated_identity(self):
        self.assertEqual(self.check(self.result())['decision'],'aceptar')
    def test_other_holder_overrides_model_acceptance(self):
        r=self.result();r['extracted']['holder_name']='Paolo Sarri'
        self.assertEqual(self.check(r)['decision'],'observar')
    def test_other_run_overrides_model_acceptance(self):
        r=self.result();r['extracted']['personal_id']='00000001-9'
        self.assertEqual(self.check(r)['decision'],'observar')
    def test_run_formatting_and_leading_zeroes(self):
        r=self.result();r['extracted']['personal_id']='000.000.004-9'
        self.assertEqual(self.check(r)['decision'],'aceptar')
    def test_expired(self):
        r=self.result();r['extracted']['expiry_date']='2020-01-01'
        self.assertEqual(self.check(r)['decision'],'observar')
    def test_missing_or_ambiguous_information_never_accepted(self):
        for field in ('holder_name','expiry_date'):
            r=self.result();r['extracted'][field]=None
            self.assertEqual(self.check(r)['decision'],'manual')
        r=self.result();r['checks']=[]
        self.assertEqual(self.check(r)['decision'],'manual')
    def test_unreadable_or_uncertain_never_rejected_automatically(self):
        r=self.result();r['confidence']=0.2;r['extracted']['holder_name']='Otro nombre'
        self.assertEqual(self.check(r)['decision'],'manual')
    def test_passport_and_alternative_have_distinct_rules(self):
        self.assertEqual(rule_key('Documento de viaje'),'pasaporte')
        self.assertEqual(rule_key('Antecedente del viaje, si corresponde'),'viaje')
        self.assertEqual(rule_key('Identificación o antecedente alternativo'),'alternativo')
        self.assertIn('Número de pasaporte',DOCUMENT_RULES['pasaporte']['fields'])
