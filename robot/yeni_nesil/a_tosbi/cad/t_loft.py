from build123d import *
import math, time
t=time.time()
def rrect_wire(w,l,r,z):
    r=min(r,w/2-0.01,l/2-0.01)
    s = RectangleRounded(w,l,r)
    return s.wires()[0].moved(Location((0,0,z)))
def pebble(W,L,T,Rc,a,b,off=0,n=10):
    z0=T/2-b
    zs=[]
    for i in range(n+1):
        t_=i/n
        zs.append(z0 + b*math.sin(t_*math.pi/2))
    zs=sorted(set([-z for z in zs]+[0]+zs))
    secs=[]
    for z in zs:
        az=abs(z)
        d=0 if az<=z0 else a*(1-math.sqrt(max(0,1-((az-z0)/b)**2)))
        if az>=T/2-1e-6: d=a-0.0
        secs.append(rrect_wire(W-2*d-2*off, L-2*d-2*off, Rc-d-off, z))
    return Solid.make_loft(secs, ruled=False)
b=pebble(80,84,44,30,26,18)
print(b.is_valid, b.volume, b.bounding_box(), time.time()-t)
export_stl(b,'t_body.stl',tolerance=0.03,angular_tolerance=0.08)
