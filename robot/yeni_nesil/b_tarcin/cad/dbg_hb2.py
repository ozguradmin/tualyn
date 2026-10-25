import sys
sys.path.insert(0,'/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/yeni/concept_B')
import model as MD
from build123d import *
hz=MD.HIP_Z
C=Vector(0, MD.P["head_y"], hz+MD.P["head_dz"])
h=MD.head_outer_solid(C)
for r in (24.5, 28, 31):
    b=MD.body_outer_solid(hz)
    nook = Pos(0, MD.P["neck_y"], hz+11) * Cylinder(r, 80, align=(Align.CENTER, Align.CENTER, Align.MIN))
    b=b-nook
    print(r,[round((MD.head_transform(p)*h).distance_to(b),2) for p in (-45,-35,0,35,45)])
