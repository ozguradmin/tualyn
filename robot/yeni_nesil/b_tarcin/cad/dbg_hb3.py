import sys
sys.path.insert(0,'/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/yeni/concept_B')
import model as MD
from build123d import *
hz=MD.HIP_Z
C=Vector(0, MD.P["head_y"], hz+MD.P["head_dz"])
h=MD.head_outer_solid(C)
for R,rz in ((36,14),(40,16),(44,18)):
    b=MD.body_outer_solid(hz)
    nook = Pos(0, MD.P["neck_y"], hz+11+rz) * MD.ellipsoid(R,R,rz)
    b=b-nook
    print(R,rz,[round((MD.head_transform(p)*h).distance_to(b),2) for p in (-40,0,40)])
