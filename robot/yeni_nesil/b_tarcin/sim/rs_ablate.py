import sys, os, json, time, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
variant, N, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
import rclib as L
xml=L.make_xml(variant, 0.6, os.path.join(HERE,'meshes_v_'+variant.replace('+','_')))
CASES=[(90,0),(180,0),(135,0),(90,20),(180,-15)]
rng=np.random.default_rng(seed); best=(-1,None); hist=[]
t0=time.time()
for t in range(N):
    seq=[L.rand_kf(rng) for _ in range(int(rng.integers(2,5)))]+[dict(L.FINAL)]
    v=[L.run_seq(xml,seq,r,p) for r,p in CASES]; sc=sum(x>0.85 for x in v)
    hist.append(sc)
    if sc>best[0]: best=(sc,seq); print(variant,t,sc,[round(x,2) for x in v],flush=True)
print(variant,'DONE n',N,'hist',np.bincount(hist,minlength=6).tolist(),'best',best[0],'wall',round(time.time()-t0),flush=True)
json.dump(dict(variant=variant,hist=hist,best=best[0],seq=best[1]),open(os.path.join(HERE,'out',f'rsab_{variant}_{seed}.json'),'w'))
