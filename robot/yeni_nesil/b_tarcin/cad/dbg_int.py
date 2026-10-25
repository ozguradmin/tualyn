import sys; sys.argv=['x']
sys.path.insert(0,'/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/yeni/concept_B')
import model as MD
from build123d import *
zc=MD.HIP_Z
inner=MD.body_outer_solid(zc,-MD.P["wall"])
d=MD.body_internals(zc)

for k,v in d.items():
    for i,s in enumerate(v.solids()):
        out=(s-inner).volume
        bb=s.bounding_box()
        print(k,i,round(out,1),[round(x,1) for x in (bb.min.X,bb.max.X,bb.min.Y,bb.max.Y,bb.min.Z-zc,bb.max.Z-zc)])
