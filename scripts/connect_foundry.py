#!/usr/bin/env python3
"""Connect an existing Azure resource to GCP without printing or saving its key."""
import argparse
import json
import os
from pathlib import Path
import subprocess

p=argparse.ArgumentParser(description=__doc__)
for name in ('project','subscription','resource-group','account','deployment'):p.add_argument('--'+name,required=True)
p.add_argument('--enable-auto',action='store_true',help='Enable automatic academic file prevalidation, not case resolution')
a=p.parse_args();gcloud=os.environ.get('GCLOUD_BIN','gcloud');az=os.environ.get('AZ_BIN','az')

def azure(*args):
    return json.loads(subprocess.run([az,*args,'--subscription',a.subscription,'-o','json'],check=True,capture_output=True,text=True).stdout)

account=azure('cognitiveservices','account','show','-g',a.resource_group,'-n',a.account)
deployment=azure('cognitiveservices','account','deployment','show','-g',a.resource_group,'-n',a.account,'--deployment-name',a.deployment)
if deployment.get('properties',{}).get('provisioningState')!='Succeeded':raise SystemExit('El modelo no está disponible.')
endpoint=account['properties']['endpoint']
key=azure('cognitiveservices','account','keys','list','-g',a.resource_group,'-n',a.account)['key1']
secret='pdi-foundry-key'
base=[gcloud,'--project='+a.project,'secrets']
exists=subprocess.run(base+['describe',secret],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
if not exists:subprocess.run(base+['create',secret,'--replication-policy=automatic'],check=True,stdout=subprocess.DEVNULL)
subprocess.run(base+['versions','add',secret,'--data-file=-'],input=key.encode(),check=True,stdout=subprocess.DEVNULL)
del key
config={'azure_openai_endpoint':endpoint,'azure_openai_deployment':a.deployment,'azure_openai_key_secret':secret,'auto_document_review':a.enable_auto}
path=Path(__file__).resolve().parents[1]/'infra'/'foundry.auto.tfvars.json'
path.write_text(json.dumps(config));path.chmod(0o600)
print('Conexión preparada. Ejecuta scripts/deploy.py --phase app para aplicar las referencias de secreto y permisos mínimos.')
