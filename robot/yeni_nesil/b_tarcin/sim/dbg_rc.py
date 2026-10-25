import sys, json, numpy as np, tarcin as T, recover as R, recover2 as R2
mu=float(sys.argv[1]); xml=T.build(mu)
plans={'A':[(False,False),(True,False)],'B':R2.PLAN,'C':[(False,False),(False,True),(True,False),(True,True)]}
cases=[('d',114.0,3.9),('d',173.1,-23.6),('d',-55.5,-2.5),('p',22,0),('d',90,0),('d',-90,0),('d',180,15)]
for name,pl in plans.items():
    out=[]
    for k,a,b in cases:
        s=T.Sim(xml,record=False)
        if k=='d':
            q=R.quat_roll_pitch(a,b); s.set_pose(R.stand(),base=(0,0,0,*q)); s.drop_to_floor(); s.d.qpos[2]+=0.015; s.hold(R.stand(),1.2)
        else:
            s.set_pose(R.stand()); s.drop_to_floor(); s.hold(R.stand(),0.4); s.d.qvel[3:6]=s.d.xmat[s.bid].reshape(3,3)@np.array([a,b,0.]); s.hold(R.stand(),1.4)
        ok,att=R2.recover(s,4,plan=pl); out.append(att if ok else -1)
    print(mu,name,out,flush=True)
