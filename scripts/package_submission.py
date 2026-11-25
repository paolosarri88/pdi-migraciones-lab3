#!/usr/bin/env python3
"""Empaqueta exclusivamente código, ejemplos sintéticos y documentación."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
files=[*root.glob('*.py')]
files += [root/n for n in ('README.md','LEEME_ENTREGA.md','Dockerfile','requirements.txt','.gitignore','.gcloudignore')]
for directory in ('static','docs','scripts','tests','examples'):
    files += [f for f in (root/directory).rglob('*') if f.is_file() and '__pycache__' not in f.parts and f.suffix not in ('.pyc','.log')]
files += [root/'infra'/n for n in ('main.tf','terraform.tfvars.example','.terraform.lock.hcl') if (root/'infra'/n).exists()]
files += list((root/'prompts').glob('*.txt'))
files=sorted(set(files))
manifest=[]
for f in files:
    rel=f.relative_to(root)
    assert f.is_file() and not f.is_symlink(),rel
    assert not any(s in rel.parts for s in ('.git','data','.venv','.terraform')),rel
    assert not any(s in f.name for s in ('.tfstate','.tfplan','.sqlite')),rel
    assert not f.name.startswith('.env'),rel
    manifest.append({'file':rel.as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
a.output.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.output,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files:z.write(f,Path('PDI_PoC')/f.relative_to(root))
    z.writestr('PDI_PoC/MANIFIESTO.json',json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps({'zip':str(a.output.resolve()),'files':len(files),'bytes':a.output.stat().st_size,'sha256':hashlib.sha256(a.output.read_bytes()).hexdigest()},ensure_ascii=False))
