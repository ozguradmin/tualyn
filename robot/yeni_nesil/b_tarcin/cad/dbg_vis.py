import sys
sys.path.insert(0,'/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/yeni/concept_B')
import model as MD
from build123d import *
C=Vector(0, MD.P["head_y"], MD.HIP_Z+MD.P["head_dz"])
hp,z=MD.head_parts(C)
o=MD.head_outer_solid(C)
for nm in ("mask","int_eyes"):
    d=hp[nm]-(o if nm=="mask" else MD.head_outer_solid(C,-1.6))
    for s in d.solids(): print(nm, round(s.volume,1), [round(v,1) for v in (s.bounding_box().min.X,s.bounding_box().max.X,s.bounding_box().min.Z-z,s.bounding_box().max.Z-z)])
