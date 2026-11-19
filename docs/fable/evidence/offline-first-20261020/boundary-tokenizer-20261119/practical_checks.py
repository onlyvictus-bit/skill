from pathlib import Path
import sys,json,hashlib,zipfile,traceback
ROOT=Path(__file__).resolve().parent;PROJECT=ROOT.parents[2];MI=Path(r'C:\Users\sakth\.codex\skills\memory-integrity');CM=Path(r'C:\Users\sakth\.codex\skills\claude-mon')
sys.path[:0]=[str(MI/'scripts'),str(CM/'scripts')]
from integrity_v2.adapters import ooxml_inventory,docling_adapter
import context_budget
fixture=ROOT/'office-ground-truth.docx'
with zipfile.ZipFile(fixture,'x') as z:
    z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
    z.writestr('word/document.xml','<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>REQ-01 Never send a live order.</w:t></w:r></w:p><w:ins><w:p><w:r><w:t>REQ-02 Changed clause requires review.</w:t></w:r></w:p></w:ins></w:body></w:document>')
    z.writestr('word/header1.xml','<w:hdr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>Header exception</w:t></w:r></w:p></w:hdr>')
    z.writestr('word/embeddings/object1.bin',b'non-executable placeholder')
inv=ooxml_inventory.inventory_ooxml(fixture);state=ooxml_inventory.readiness(inv);assert state=='PARTIAL';assert {i['kind'] for i in inv['parts']}=={'word-body','word-header-footer'};assert len(inv['unsupported'])==2
checks={'office_inventory':{'source_sha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'inventory':inv,'state':state,'expected':'PARTIAL due to tracked change and embedded object','verdict':'EXPECTED_REFUSAL','text_conversion_executed':False},'docling':docling_adapter.qualify()}
try:docling_adapter.convert(fixture)
except docling_adapter.DoclingError:checks['conversion_refusal']={'verdict':'EXPECTED_REFUSAL','cause':traceback.format_exc()}
else:raise AssertionError('unexpected converter execution')
checks['reserve_arithmetic']={'batches':context_budget.schedule_batches([('A',5),('B',6)],context_limit=12,reserved_output_tokens=2,fixed_overhead_tokens=1),'real_tokenizer':False};assert checks['reserve_arithmetic']['batches']==[['A'],['B']]
try:context_budget.count_tokens('exact token test',explicit_encoding='cl100k_base')
except context_budget.BudgetError:checks['exact_counting']={'verdict':'BLOCKED','cause':traceback.format_exc()}
else:raise AssertionError('unexpected real tokenizer')
(ROOT/'Practical-Checks.json').write_bytes((json.dumps(checks,indent=2)+'\n').encode());print('OFFICE_INVENTORY_REFUSAL_PASS; CONVERTER_UNAVAILABLE; RESERVE_ARITHMETIC_PASS; EXACT_TOKENIZER_BLOCKED')
