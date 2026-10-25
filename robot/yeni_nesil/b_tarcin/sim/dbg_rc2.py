import sys, json, numpy as np, tarcin as T, recover as R, recover2 as R2
mu=float(sys.argv[1]); R2.MIRROR_SIDE = sys.argv[2]=='1'; xml=T.build(mu)
rng=np.random.default_rng(11); o11=[(float(rng.uniform(-180,180)),float(rng.uniform(-40,40))) for _ in range(24)]
cases=[('d',180,0),('d',180,15),('d',178.4,20.5),('d',*o11[4]),('p',22,0),('p',-22,0),('d',90,0),('d',-90,0),('d',*o11[9])]
out=[]
for k,a,b in cases:
    s=T.Sim(xml,record=False)
    if k=='d':
        q=R.quat_roll_pitch(a,b); s.set_pose(R.stand(),base=(0,0,0,*q)); s.drop_to_floor(); s.d.qpos[2]+=0.015; s.hold(R.stand(),1.2)
    else:
        s.set_pose(R.stand()); s.drop_to_floor(); s.hold(R.stand(),0.4); s.d.qvel[3:6]=s.d.xmat[s.bid].reshape(3,3)@np.array([a,b,0.]); s.hold(R.stand(),1.4)
    log=[]; ok,att=R2.recover(s,4,log=log); out.append((att if ok else -1, [(l['state'][0],l['down']) for l in log]))
print(mu,'mirror_side',R2.MIRROR_SIDE,out,flush=True)
