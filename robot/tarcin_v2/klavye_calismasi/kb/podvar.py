import sys, json; sys.path.insert(0,'.')
import kbsim
var=json.loads(sys.argv[1]); kbsim.VARIANT.update(var)
import podclr, rgait
res=[]
for spread in [0.0, 0.010]:
    for H in [0.005,0.008,0.010,0.012,0.015,0.020]:
        sp={"gait":"trot","H":H,"a":0.0,"stride":0.02,"duty":0.5,"fy":-spread,"hy":spread}
        R=rgait.Rough(sp); p=R.p
        def fn(leg,u):
            y0,z0=R.rf[leg]; y0+=p['fy'] if leg[0]=='f' else p['hy']
            ph=(u+rgait.PH['trot'][leg])%1.0
            return R.foot(leg,ph,p['stride'],p['H'],z0,y0)
        res.append(f"spread{spread*1000:.0f} H{H*1000:.0f}:{podclr.clearance(fn)[0]:5.1f}")
print(var, ' '.join(res))
