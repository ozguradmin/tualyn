import sys, os, math, json, time, numpy as np, mujoco
HERE=os.path.dirname(os.path.abspath(__file__))
sys.argv=[sys.argv[0], os.path.join(HERE,'best_seq_13.json')]
os.chdir(HERE)
sys.path.insert(0,HERE)
import verify as V
m=mujoco.MjModel.from_xml_string(V.base)
for ro,pi in [(90,0),(-90,0),(135,0)]:
    t=time.time(); print(ro,pi,V.run(m,ro,pi), round(time.time()-t,1), flush=True)
