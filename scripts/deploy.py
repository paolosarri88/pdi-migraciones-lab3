#!/usr/bin/env python3
"""Despliegue reproducible: Terraform, Cloud Build y Cloud Run.

Requiere gcloud autenticado y Terraform en PATH, o GCLOUD_BIN/TERRAFORM_BIN.
El proyecto debe existir y estar vinculado a la cuenta educativa.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--project', required=True)
parser.add_argument('--billing-account', required=True)
parser.add_argument('--region', default='us-central1')
parser.add_argument('--phase', choices=['foundation','app','all'], default='all')
parser.add_argument('--image', help='Reutilizar una imagen ya compilada y verificada, sin recompilar.')
args = parser.parse_args()
gcloud = os.environ.get('GCLOUD_BIN','gcloud')
terraform = os.environ.get('TERRAFORM_BIN','terraform')
env = os.environ.copy()
env.update(TF_VAR_project_id=args.project, TF_VAR_billing_account=args.billing_account, TF_VAR_region=args.region)

def run(command, *, capture=False):
    return subprocess.run(command, cwd=ROOT, env=env, check=True,
                          text=True, stdout=subprocess.PIPE if capture else None).stdout

def tf(*command, capture=False):
    # Never write the OAuth token into configuration files, logs or Terraform state.
    env['GOOGLE_OAUTH_ACCESS_TOKEN'] = run([gcloud,'auth','print-access-token'],capture=True).strip()
    try:
        return run([terraform,'-chdir=infra',*command],capture=capture)
    finally:
        env.pop('GOOGLE_OAUTH_ACCESS_TOKEN',None)

os.umask(0o077)
run([terraform,'-chdir=infra','init','-input=false','-no-color'])
if args.phase in ('foundation','all'):
    # Preserve an existing deployment if this command is run again later.
    saved = ROOT/'infra'/'deployment.auto.tfvars.json'
    if not saved.exists():
        saved.write_text(json.dumps({'deploy_app':False}))
    tf('plan','-input=false','-out=foundation.tfplan','-no-color')
    tf('apply','-input=false','-no-color','foundation.tfplan')
if args.phase in ('app','all'):
    image=args.image
    if not image:
        outputs=json.loads(tf('output','-json',capture=True))
        stamp=datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        image=outputs['image_repository']['value']+':'+stamp
        run([gcloud,'builds','submit','.', '--project='+args.project, '--region='+args.region,
             '--tag='+image, '--service-account=projects/'+args.project+'/serviceAccounts/'+outputs['build_account']['value'],
             '--gcs-source-staging-dir=gs://'+outputs['build_bucket']['value']+'/source',
             '--gcs-log-dir=gs://'+outputs['build_bucket']['value']+'/logs','--quiet'])
    # Persist the selected image for future plans and normal updates.
    (ROOT/'infra'/'deployment.auto.tfvars.json').write_text(json.dumps({'deploy_app':True,'image':image}))
    tf('plan','-input=false','-out=application.tfplan','-no-color')
    tf('apply','-input=false','-no-color','application.tfplan')
    print('URL del portal:',tf('output','-raw','url',capture=True))
