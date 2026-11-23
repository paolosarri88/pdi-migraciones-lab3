"""Lectura visual opcional con Foundry; nunca simula un resultado del proveedor."""
import base64
import json
import os
from pathlib import Path
import urllib.request
from urllib.parse import quote, urlparse
from document_rules import DOCUMENT_RULES, rule_key

RULE_VERSION='academico-v1'

def enabled():
    return os.environ.get('AUTO_DOCUMENT_REVIEW')=='1' and all(os.environ.get(k) for k in ('AZURE_OPENAI_ENDPOINT','AZURE_OPENAI_API_KEY','AZURE_OPENAI_DEPLOYMENT'))

def normalize_result(result, rule):
    if not isinstance(result,dict):raise ValueError('Respuesta no válida')
    decision=result.get('decision');confidence=result.get('confidence')
    if decision not in ('aceptar','observar','manual') or type(confidence) not in (float,int) or not 0<=confidence<=1:raise ValueError('Decisión no válida')
    if not isinstance(result.get('reason'),str) or not result['reason'].strip():raise ValueError('Falta explicación')
    checks=result.get('checks')
    if not isinstance(checks,list) or len(checks)>20:raise ValueError('Faltan criterios')
    valid_checks={}
    for check in checks:
        if not isinstance(check,dict) or not isinstance(check.get('field'),str) or type(check.get('present')) is not bool or not isinstance(check.get('evidence'),str):raise ValueError('Criterio no válido')
        if check['field'] in valid_checks:raise ValueError('Criterio repetido')
        valid_checks[check['field']]=check
    all_present=all(valid_checks.get(f,{}).get('present') is True and valid_checks[f]['evidence'].strip() for f in rule['fields'])
    type_matches=result.get('document_type_matches');legible=result.get('legible')
    if type(type_matches) is not bool or type(legible) is not bool:raise ValueError('Falta clasificación')
    # A confidence threshold alone never authorizes acceptance.
    if confidence<0.9 or (decision=='aceptar' and not (all_present and type_matches and legible)) or not legible:
        decision='manual'
    return {'decision':decision,'confidence':confidence,'checks':checks,'reason':result['reason'][:1000],'rules_version':RULE_VERSION,'source':'Microsoft Foundry','model':os.environ.get('AZURE_OPENAI_DEPLOYMENT','')}

def inspect_document(raw,mime,requirement):
    if not enabled():return None
    rule=DOCUMENT_RULES[rule_key(requirement)]
    import pymupdf as fitz
    with fitz.open(stream=raw,filetype={'application/pdf':'pdf','image/png':'png','image/jpeg':'jpeg'}[mime]) as doc:
        if doc.is_encrypted or not 1<=len(doc)<=3:return {'decision':'manual','reason':'El archivo necesita revisión manual: está protegido o supera tres páginas.','rules_version':RULE_VERSION,'source':'Control de lectura local'}
        images=[]
        for page in doc:
            width,height=page.rect.width,page.rect.height
            if width<=0 or height<=0:return {'decision':'manual','reason':'No se pudieron leer las dimensiones del archivo.','source':'Control de lectura local','rules_version':RULE_VERSION}
            scale=min(2,1600/max(width,height))
            pix=page.get_pixmap(matrix=fitz.Matrix(scale,scale),colorspace=fitz.csRGB,alpha=False)
            images.append({'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(pix.tobytes('png')).decode(),'detail':'high'}})
    instructions=(Path(__file__).parent/'prompts'/'revision-documental.txt').read_text()
    content=[{'type':'text','text':json.dumps({'requisito':requirement,'descripcion':rule['description'],'campos':rule['fields'],'criterios_version':RULE_VERSION},ensure_ascii=False)}]+images
    payload={'messages':[{'role':'system','content':instructions},{'role':'user','content':content}],'response_format':{'type':'json_object'},'max_tokens':1100,'temperature':0}
    endpoint=os.environ['AZURE_OPENAI_ENDPOINT'].rstrip('/')
    parsed=urlparse(endpoint)
    if parsed.scheme!='https' or parsed.hostname is None or not parsed.hostname.endswith(('.openai.azure.com','.services.ai.azure.com','.cognitiveservices.azure.com')):raise ValueError('Endpoint Azure no permitido')
    url=endpoint+'/openai/deployments/'+quote(os.environ['AZURE_OPENAI_DEPLOYMENT'],safe='')+'/chat/completions?api-version=2024-10-21'
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','api-key':os.environ['AZURE_OPENAI_API_KEY']})
    with urllib.request.urlopen(req,timeout=35) as response:
        body=json.loads(response.read(1024*1024))
    return normalize_result(json.loads(body['choices'][0]['message']['content']),rule)
