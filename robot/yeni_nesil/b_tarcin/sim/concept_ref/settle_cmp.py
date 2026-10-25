import sys, os, math, json, numpy as np, mujoco
HERE=os.path.dirname(os.path.abspath(__file__))
sys.argv=[sys.argv[0], os.path.join(HERE,'stl')]
sys.path.insert(0,HERE)
import righting as R
R.build_xml()
m=mujoco.MjModel.from_xml_path(os.path.join(R.OUT,'tarcin.xml'))
for roll,pitch in [(90,0),(-90,0),(135,0),(180,0)]:
    r=R.Runner(m); r.set_orientation(roll,pitch); r.step_to(r.target,1.2)
    x,y,z=r.axes(); d=r.d
    cs=set()
    for i in range(d.ncon):
        c=d.contact[i]; g=[c.geom1,c.geom2]
        cs.add(tuple(m.body(m.geom_bodyid[k]).name for k in g))
    print('concept',roll,pitch,'up',round(z[2],2),'side',round(x[2],2),sorted(cs))
