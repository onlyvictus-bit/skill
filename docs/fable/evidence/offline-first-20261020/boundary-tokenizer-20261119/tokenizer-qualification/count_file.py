"""Read-only counter using the qualified runtime and unchanged installed Claude-Mon code."""
from pathlib import Path
import argparse,sys,json,os,hashlib,importlib.util,importlib.metadata
ROOT=Path(__file__).resolve().parent
MODULE=Path(r'C:\Users\sakth\.codex\skills\claude-mon\scripts\context_budget.py')
MODULE_SHA='717b62c3f09566c1a8f6f9e844963637eb6c42dfeced6c8012aa0923119bd888'
CACHE_FILES=[{'path': '9b5ad71b2ce5302211f9c61530b329a4922fc6a4', 'size': 1681126, 'sha256': '223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7'}, {'path': 'fb374d419588a4632f3f557e76b4b70aebbca790', 'size': 3613922, 'sha256': '446a9538cb6c348e3516120d7c08b09f57c36495e2acfffe59a5bf8b0cfb1a2d'}]
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--input',type=Path,required=True);parser.add_argument('--encoding',choices=['cl100k_base','o200k_base'],required=True);parser.add_argument('--context-limit',type=int,required=True);parser.add_argument('--reserved-output',type=int,required=True);parser.add_argument('--overhead',type=int,required=True);args=parser.parse_args()
    try:
        if Path(sys.prefix).resolve()!=(ROOT/'venv').resolve():raise ValueError('Use the qualified venv/Scripts/python.exe')
        if hashlib.sha256(MODULE.read_bytes()).hexdigest()!=MODULE_SHA:raise ValueError('Installed budgeting code changed; requalification required')
        for row in CACHE_FILES:
            p=ROOT/'encodings'/row['path']
            if p.stat().st_size!=row['size'] or hashlib.sha256(p.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('Encoding cache changed; requalification required')
        os.environ['TIKTOKEN_CACHE_DIR']=str(ROOT/'encodings')
        def guard(event,values):
            if event in ('socket.connect','socket.getaddrinfo','socket.bind'):raise PermissionError('QUALIFIED_COUNTER_NETWORK_DISABLED')
        sys.addaudithook(guard)
        if importlib.metadata.version('tiktoken')!='0.14.0':raise ValueError('Tokenizer version changed')
        spec=importlib.util.spec_from_file_location('qualified_installed_cm_budget',MODULE);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        raw=args.input.read_bytes();text=raw.decode('utf-8');count=module.count_tokens(text,explicit_encoding=args.encoding)
        module.schedule_batches([('input',count)],context_limit=args.context_limit,reserved_output_tokens=args.reserved_output,fixed_overhead_tokens=args.overhead)
        print(json.dumps({'ok':True,'input':str(args.input.resolve()),'source_sha256':hashlib.sha256(raw).hexdigest(),'encoding':args.encoding,'tiktoken':'0.14.0','input_tokens':count,'context_limit':args.context_limit,'reserved_output':args.reserved_output,'declared_overhead':args.overhead,'fits_declared_budget':True,'scope':'exact local file tokens; caller-declared reserves; excludes undisclosed model/provider framing'},ensure_ascii=False));return 0
    except Exception as error:
        print(json.dumps({'ok':False,'error':type(error).__name__,'detail':str(error),'truncated':False}));return 2
if __name__=='__main__':raise SystemExit(main())
