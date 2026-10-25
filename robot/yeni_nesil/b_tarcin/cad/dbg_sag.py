import sys, math
sys.path.insert(0,'/tmp/claude-0/-home-user-tualyn/088f8e83-392a-5b19-ac2c-5c0005fbdef6/scratchpad/yeni/concept_B')
import model as MD
from build123d import *
for eh,ev in [(2.8,2.55),(3.4,2.55),(3.4,2.9),(4.0,2.9),(3.6,3.2)]:
    hw,hd,hh=MD.P["head"]
    o=Pos(0,-48,105)*MD.superellipsoid(hw,hd,hh,eh=eh,ev=ev)
    ze=103.5
    sy=lambda x,z: MD.surface_y(o,x,z,-48-hd-2,-48)
    for ex in (20,):
        c=Vector(ex,sy(ex,ze),ze)
        px1,px0=Vector(ex+3,sy(ex+3,ze),ze),Vector(ex-3,sy(ex-3,ze),ze)
        pz1,pz0=Vector(ex,sy(ex,ze+3),ze+3),Vector(ex,sy(ex,ze-3),ze-3)
        n=(pz1-pz0).cross(px1-px0).normalized()
        if n.Y>0: n=-n
        xd=Vector(0,0,1).cross(n).normalized(); yd=n.cross(xd)
        def sag(r):
            h=0
            for k in range(24):
                t=2*math.pi*k/24; q=c+xd*(r*math.cos(t))+yd*(r*math.sin(t)); p=Vector(q.X,sy(q.X,q.Z),q.Z); h=min(h,(p-c).dot(n))
            return -h
        print(eh,ev,'toe',round(math.degrees(math.atan2(n.X,-n.Y)),1),'sag16',round(sag(16),2),'sag20.8',round(sag(20.8),2))
