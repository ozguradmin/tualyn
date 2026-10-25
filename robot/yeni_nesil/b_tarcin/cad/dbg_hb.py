import sys
sys.path.insert(0,'/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/yeni/concept_B')
import model as MD
from build123d import *
hz=MD.HIP_Z
b=MD.body_outer_solid(hz)
for dy,dz in [(0,0),(-2,1),(-3,2),(0,3)]:
    C=Vector(0, MD.P["head_y"]+dy, hz+MD.P["head_dz"]+dz)
    h=MD.head_outer_solid(C)
    print(dy,dz,[round((MD.head_transform(p)*h).distance_to(b),2) if (MD.head_transform(p)*h).distance_to(b)>0 else -round(((MD.head_transform(p)*h)&b).volume,1) for p in (-45,-25,0,25,45)])
