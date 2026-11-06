"""Recompute published summaries without rerunning any benchmarks (stdlib only)."""
from pathlib import Path
import csv,json,hashlib,statistics as st,math,random
ROOT=Path(__file__).resolve().parents[1]
def read(path):
    with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def main():
    original=read(ROOT/'data/original/results.csv')
    expected=[(i,w,r) for r in range(1,10) for i in [1000,10000,100000] for w in [1,2,4,8,16]]
    random.Random(2026).shuffle(expected)
    assert [(int(x['iterations']),int(x['workers']),int(x['repeat'])) for x in original]==expected
    expected_follow={(i,w,r,mode) for i,w,r in expected for mode in ['fresh','prewarmed']}
    summary=[];paired=[]
    for session in ['original','session_1','session_2']:
        folder=ROOT/'data'/session
        rows=original if session=='original' else read(folder/'timings.csv')
        if session!='original':
            meta=json.loads((folder/'metadata.json').read_text())
            assert meta['status']=='complete' and len(rows)==270 and all(x['verified']=='True' for x in rows)
            assert hashlib.sha256((folder/'timings.csv').read_bytes()).hexdigest()==meta['timings_sha256']
            assert hashlib.sha256((folder/'pool_comparison.py').read_bytes()).hexdigest()==meta['script_sha256']
            assert {(int(x['iterations']),int(x['workers']),int(x['repeat']),x['mode']) for x in rows}==expected_follow
        for i in [1000,10000,100000]:
            for w in [1,2,4,8,16]:
                z=[x for x in rows if int(x['iterations'])==i and int(x['workers'])==w]
                for mode in (['fresh'] if session=='original' else ['fresh','prewarmed']):
                    v=[float(x['duration_seconds'])*1000 for x in z if session=='original' or x['mode']==mode]
                    assert len(v)==9 and all(math.isfinite(t) and t>0 for t in v)
                    summary.append(dict(session=session,iterations=i,workers=w,mode=mode,n=9,median_ms=st.median(v),min_ms=min(v),max_ms=max(v)))
                if session!='original':
                    diff=[]
                    for rep in range(1,10):
                        pair={x['mode']:float(x['duration_seconds'])*1000 for x in z if int(x['repeat'])==rep}
                        diff.append(pair['fresh']-pair['prewarmed'])
                    f=st.median(float(x['duration_seconds'])*1000 for x in z if x['mode']=='fresh')
                    h=st.median(float(x['duration_seconds'])*1000 for x in z if x['mode']=='prewarmed')
                    paired.append(dict(session=session,iterations=i,workers=w,median_paired_difference_ms=st.median(diff),prewarmed_faster_pairs=sum(t>0 for t in diff),pairs=9,median_time_reduction_percent=100*(1-h/f)))
    out=ROOT/'analysis';out.mkdir(exist_ok=True)
    for name,rows in [('summary.csv',summary),('paired_summary.csv',paired)]:
        with (out/name).open('w',newline='',encoding='utf-8') as f:
            wr=csv.DictWriter(f,fieldnames=list(rows[0]));wr.writeheader();wr.writerows(rows)
    print('PASS: original 135 runs; two follow-ups of 270 each; balanced cells; recorded verification; file hashes. Summaries written to analysis/.')
if __name__=='__main__':main()
