import sys, os
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import ablate as A, recover as R
for opts in [['soft','tail8','paw','nohub','unimass'],['soft']]:
    x=A.make(opts).replace('forcerange="-0.06 0.06"','forcerange="-0.2 0.2"')
    res=[R.drop_case(x,r,p,tries=1) for r,p in A.CASES]
    print('pan0.2+'+'+'.join(opts), sum(c['ok'] for c in res), [c['settled_up'] for c in res], flush=True)
