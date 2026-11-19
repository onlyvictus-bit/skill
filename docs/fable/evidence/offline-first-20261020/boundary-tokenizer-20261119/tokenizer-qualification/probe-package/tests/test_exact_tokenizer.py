from pathlib import Path
import hashlib,importlib.util,json,os,sys,unittest
ROOT=Path(__file__).resolve().parents[2];CM=Path(r'C:\Users\sakth\.codex\skills\claude-mon');os.environ['TIKTOKEN_CACHE_DIR']=str(ROOT/'encodings')
# Encoding assets are already cached. No test may silently download anything.
def network_guard(event,args):
    if event in ('socket.connect','socket.getaddrinfo','socket.bind'):raise PermissionError('TOKENIZER_QUALIFICATION_NETWORK_DISABLED: '+event)
sys.addaudithook(network_guard)
import tiktoken
spec=importlib.util.spec_from_file_location('installed_cm_context_budget',CM/'scripts/context_budget.py');legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)
sys.path.insert(0,str(CM/'scripts'));from complete_read_v2 import budget
ENCODINGS=('cl100k_base','o200k_base')
def profile(enc='cl100k_base',limit=1000,output=200):return {'schema_version':2,'provider':'offline-qualification','model':'explicit-encoding-fixture','encoding':enc,'encoding_version':'tiktoken-0.14.0','context_limit':limit,'output_limit':output,'counting_method':'tiktoken'}
class ExactTokenizer(unittest.TestCase):
    def test_exact_installed_module_paths(self):
        self.assertEqual(Path(legacy.__file__).resolve(),(CM/'scripts/context_budget.py').resolve());self.assertEqual(Path(budget.__file__).resolve(),(CM/'scripts/complete_read_v2/budget.py').resolve())
    def test_known_cl100k_reference_vector(self):
        self.assertEqual(tiktoken.get_encoding('cl100k_base').encode('hello world'),[15339,1917]);self.assertEqual(legacy.count_tokens('hello world',explicit_encoding='cl100k_base'),2)
    def test_multilingual_exact_counts_and_reassembly(self):
        corpus=['','hello world','தமிழ் நினைவகச் சோதனை','日本語の文章','👩🏽‍💻🚀','e\u0301 café\r\nnext\tline', 'def f(x):\n    return x + 1\n']
        for enc_name in ENCODINGS:
            enc=tiktoken.get_encoding(enc_name)
            for text in corpus:
                with self.subTest(encoding=enc_name,text=text):
                    tokens=enc.encode_ordinary(text);self.assertEqual(enc.decode(tokens),text);self.assertEqual(legacy.count_tokens(text,explicit_encoding=enc_name),len(tokens));count,method=budget.count_tokens(text,enc_name);self.assertEqual((count,method),(len(tokens),'tiktoken:'+enc_name))
    def test_unknown_model_refused(self):
        with self.assertRaisesRegex(legacy.BudgetError,'unknown model tokenizer mapping'):legacy.count_tokens('hello',model='qualification-unknown-model-7cd5')
    def test_unknown_encoding_refused_by_both_routes(self):
        with self.assertRaises(ValueError):legacy.count_tokens('hello',explicit_encoding='qualification-invalid-encoding')
        with self.assertRaisesRegex(budget.BudgetError,'E_TOKENIZER_ENCODING'):budget.count_tokens('hello','qualification-invalid-encoding')
    def test_missing_model_and_encoding_refused(self):
        with self.assertRaisesRegex(legacy.BudgetError,'model or explicit_encoding'):legacy.count_tokens('hello')
    def test_special_marker_is_not_silently_lost(self):
        text='<|endoftext|>'
        for name in ENCODINGS:
            with self.subTest(encoding=name):
                with self.assertRaises(ValueError):legacy.count_tokens(text,explicit_encoding=name)
                count,method=budget.count_tokens(text,name);self.assertEqual(count,len(tiktoken.get_encoding(name).encode_ordinary(text)));self.assertGreater(count,0)
    def test_complete_section_breakdown_real_counter(self):
        sections={'instructions':'Review every required unit.','source':'தமிழ் project requirements\nDo not send orders.','task':'Preserve exceptions.'}
        for name in ENCODINGS:
            expected={k:len(tiktoken.get_encoding(name).encode_ordinary(v)) for k,v in sections.items()};v=budget.measure_request(profile(name),sections);self.assertEqual(v['breakdown'],expected);self.assertEqual(v['input_tokens'],sum(expected.values()));self.assertEqual(v['methods'],['tiktoken:'+name]);self.assertEqual(v['scope'],'local-text-excluding-provider-framing')
    def test_exact_fit_and_plus_one_with_actual_count(self):
        for name in ENCODINGS:
            count,_=budget.count_tokens('hello world',name);p=profile(name,count+4,4);units=[{'id':'U1','input_tokens':count}];self.assertEqual(budget.plan_batches(p,units,per_unit_output=2,reasoning_reserve=1,safety_reserve=1)['batches'],[['U1']])
            with self.assertRaises(budget.BudgetError):budget.plan_batches(profile(name,count+3,4),units,per_unit_output=2,reasoning_reserve=1,safety_reserve=1)
    def test_large_actual_input_refused_without_mutation(self):
        text=('தமிழ் source sentence.\n'*2000);before=hashlib.sha256(text.encode()).hexdigest()
        for name in ENCODINGS:
            count,_=budget.count_tokens(text,name);self.assertGreater(count,1000)
            with self.assertRaises(budget.BudgetError):budget.plan_batches(profile(name),[{'id':'U1','input_tokens':count}],per_unit_output=20)
        self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),before)
    def test_batching_keeps_every_real_counted_unit(self):
        texts=['alpha beta','தமிழ்','日本語','one two three','emoji 🚀']
        for name in ENCODINGS:
            items=[(str(i),budget.count_tokens(text,name)[0]) for i,text in enumerate(texts)];limit=max(v for _,v in items)+5
            batches=legacy.schedule_batches(items,context_limit=limit,reserved_output_tokens=3,fixed_overhead_tokens=2);self.assertEqual([i for b in batches for i in b],[i for i,_ in items])
            for b in batches:self.assertLessEqual(sum(dict(items)[i] for i in b)+5,limit)
    def test_output_limit_splits_even_when_input_fits(self):
        count,_=budget.count_tokens('hello','cl100k_base');units=[{'id':str(i),'input_tokens':count} for i in range(3)];v=budget.plan_batches(profile(output=20),units,per_unit_output=11);self.assertEqual(v['batches'],[['0'],['1'],['2']])
    def test_duplicate_unit_is_not_counted_twice(self):
        with self.assertRaisesRegex(budget.BudgetError,'E_BATCH_DUPLICATE'):budget.plan_batches(profile(),[{'id':'U1','input_tokens':1},{'id':'U1','input_tokens':1}],per_unit_output=2)
    def test_no_network_needed_for_encoding_reopen(self):
        import socket
        with self.assertRaisesRegex(PermissionError,'NETWORK_DISABLED'):socket.getaddrinfo('example.com',443)
        for name in ENCODINGS:self.assertEqual(tiktoken.get_encoding(name).decode(tiktoken.get_encoding(name).encode_ordinary('cached தமிழ்')),'cached தமிழ்')
