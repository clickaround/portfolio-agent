#!/usr/bin/env python3
"""Optional JSON Schema semantics check. Requires `jsonschema` (NOT in zero-dep static validator)."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def main():
 try:from jsonschema import Draft202012Validator
 except ImportError:
  print('CONTRACT_SCHEMA_CHECK: SKIPPED (install the optional jsonschema package only if approved)')
  return 3
 files={
  'cases/case.schema.json':['cases/fixtures/synthetic-case.json'],
  'contracts/asset-manifest.schema.json':['examples/SYNTHETIC_asset-manifest.json'],
  'contracts/book-plan.schema.json':['examples/SYNTHETIC_book-plan.json'],
  'contracts/scene-document.schema.json':['examples/SYNTHETIC_scene.json','examples/SYNTHETIC_scene_invalid.json'],
 }
 errors=[];count=0
 for schema,instances in files.items():
  s=json.loads((ROOT/schema).read_text(encoding='utf-8'));Draft202012Validator.check_schema(s)
  for inst in instances:
   data=json.loads((ROOT/inst).read_text(encoding='utf-8'));es=list(Draft202012Validator(s).iter_errors(data))
   if es:errors.extend(f'{inst}: {e.message}' for e in es)
   else:count+=1
 print(f'CONTRACT_SCHEMA_CHECK: {"PASS" if not errors else "FAIL"}; validated={count}, errors={len(errors)}')
 for e in errors:print(' - '+e)
 return 1 if errors else 0
if __name__=='__main__':raise SystemExit(main())
