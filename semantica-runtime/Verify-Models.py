"""Reopen and hash all selected model files without inference or network calls."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'memory-integrity/scripts'))
from knowledge_bridge.model_runtime import load_manifest
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--manifest',type=Path,required=True);args=parser.parse_args()
    try:
        result=load_manifest(args.manifest)
        print(json.dumps({'ok':True,'manifest_digest':result['manifest_digest'],'models':{role:{'model_id':model['model_id'],'revision':model['revision'],'files':len(model['files'])} for role,model in result['models'].items()}}))
    except Exception as exc:print(json.dumps({'ok':False,'error':str(exc)}));sys.exit(2)
