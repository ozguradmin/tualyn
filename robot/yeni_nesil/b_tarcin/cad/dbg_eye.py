import sys
sys.path.insert(0,'/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/yeni/concept_B')
import model as MD
from build123d import *
C=Vector(0, MD.P["head_y"], MD.HIP_Z+MD.P["head_dz"])
hp,z=MD.head_parts(C)
hin=MD.head_outer_solid(C,-1.6)
for i,s in enumerate(hp["int_eyes"].solids()):
    bb=s.bounding_box(); print(i, round((s-hin).volume,1), bb)
d=hp["int_eyes"]-hin
for s in d.solids(): print('out piece', round(s.volume,1), s.bounding_box())
print('front surface y at centre', MD.surface_y(MD.head_outer_solid(C),0,z,-90,-48), 'z_eye',z)
