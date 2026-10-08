"""Observed-loss diagnostics and narrow structured proposition comparison.

Caller stage lists are MANUAL_REPORTED. Exact-request/CAS observation is supplied
by trace_adapter, not implied by claim IDs. This is never a universal truth score.
"""
from . import contracts as c

CLAIM_FIELDS={'id','text','polarity','conditions','source_units'}

def claims(rows):
    if not isinstance(rows,list): raise ValueError('E_CLAIMS')
    seen=set()
    for r in rows:
        c.keys(r,CLAIM_FIELDS,'claim');c.identity(r['id'],'claim');c.string(r['text'],'claim text');c.strings(r['conditions'],'claim conditions')
        if r['id'] in seen or r['polarity'] not in ('positive','negative','unknown'): raise ValueError('E_CLAIM_ID_STATE')
        if not isinstance(r['source_units'],list) or not r['source_units']: raise ValueError('E_CLAIM_SOURCE')
        for ref in r['source_units']: c.keys(ref,{'source_id','unit_id'},'claim source')
        seen.add(r['id'])
    return {r['id']:r for r in rows}

def same(a,b): return all(a[k]==b[k] for k in ('text','polarity','conditions','source_units'))

def audit(expected,stages):
    oracle=claims(expected)
    if not oracle: raise ValueError('E_EXPECTED_EMPTY: independent requirement oracle required')
    if set(stages)!={'source','retrieval','prompt','answer'}: raise ValueError('E_STAGE_SCOPE')
    observed={};limitations=[];findings=[]
    for name,row in stages.items():
        if row is None: observed[name]=None;limitations.append(name)
        elif isinstance(row,dict):
            c.keys(row,{'state','claims'},'stage')
            if row['state'] not in ('OBSERVED','PARTIAL','FAILED','UNOBSERVED'): raise ValueError('E_STAGE_STATE')
            observed[name]=claims(row['claims']) if row['state'] in ('OBSERVED','PARTIAL') else None
            if row['state']!='OBSERVED': limitations.append(name)
        else: observed[name]=claims(row)
    for ident,e in oracle.items():
        for name in ('source','retrieval','prompt','answer'):
            current=observed[name]
            if name!='retrieval' and current is not None and name not in limitations and ident not in current:
                findings.append({'kind':'REQUIRED_CLAIM_MISSING','claim_id':ident,'stage':name})
            elif current is not None and ident in current and not same(e,current[ident]):
                findings.append({'kind':'SOURCE_MISMATCH' if name=='source' else 'PROPOSITION_MISMATCH','claim_id':ident,'stage':name})
        previous=None
        for name in ('source','retrieval','prompt','answer'):
            current=observed[name]
            # An incomplete observation cannot establish absence or a loss.
            # Positive mismatches above remain evidence even in PARTIAL data.
            if current is None or name in limitations: previous=None;continue
            if ident not in current and previous is not None and ident in previous:
                findings.append({'kind':'CONTEXT_GAP' if name=='prompt' else 'OBSERVED_LOSS','claim_id':ident,'stage':name,'causation':'UNPROVEN; alternate tool/derivation paths may exist'})
            previous=current
    answer,prompt,source=(observed[n] for n in ('answer','prompt','source'))
    for ident,a in (answer or {}).items():
        if ident not in oracle: findings.append({'kind':'UNSUPPORTED','claim_id':ident,'stage':'answer'})
        elif not same(a,oracle[ident]): findings.append({'kind':'CONTRADICTION','claim_id':ident,'stage':'answer','detail':'structured proposition/polarity/conditions/source references differ'})
    def ratio(num,den): return num/den if den else None
    full=lambda name: name not in limitations
    metrics={'prompt_inclusion':ratio(sum(i in (prompt or {}) for i in oracle),len(oracle)) if full('prompt') else None,
             'answer_coverage':ratio(sum(i in (answer or {}) and same(e,answer[i]) for i,e in oracle.items()),len(oracle)) if full('answer') else None,
             'source_support':ratio(sum(i in (source or {}) and i in oracle and same(a,source[i]) and same(a,oracle[i]) for i,a in (answer or {}).items()),len(answer or {})) if full('source') and full('answer') else None,
             'prompt_id_overlap':ratio(len(set(answer or {})&set(prompt or {})),len(answer or {})) if full('prompt') and full('answer') else None}
    return {'ok':not findings and not limitations,'verdict':'PASSED_FOR_DECLARED_STRUCTURED_CHECKS' if not findings and not limitations else 'BLOCKED','evidence_class':'MANUAL_REPORTED','expected_denominator':len(oracle),'metrics':metrics,'findings':findings,'limitations':sorted(set(limitations)),'semantic_truth':'UNVERIFIED','metric_scope':'identity transport and exact curated proposition agreement; no free-text semantic proof'}
