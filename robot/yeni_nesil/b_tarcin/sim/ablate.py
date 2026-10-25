import sys, os, re, itertools, json
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import tarcin as T, recover as R
T.MESHDIR=os.path.join(HERE,'meshes_ab'); os.makedirs(T.MESHDIR,exist_ok=True)
CASES=[(90,0),(-90,0),(135,0),(-135,0),(90,20),(45.0,27.8),(99.2,-19.2),(-102.5,-23.8)]
def make(opts):
    T.COLLIDE['body']=['shell','cream','charcoal'] if 'nohub' in opts else ['shell','cream','charcoal','hub']
    x=T.build(mu=0.6, ears='soft' if 'soft' in opts else 'rigid')
    if 'tail8' in opts: x=x.replace('name="tail_hull" type="mesh" mesh="tail" mass="0.01410"','name="tail_hull" type="mesh" mesh="tail" mass="0.00810"')
    if 'paw' in opts:
        x=re.sub(r'    <pair[^\n]*\n','',x); x=x.replace(' priority="1"','')
        x=x.replace('contype="2" conaffinity="2"','contype="2" conaffinity="2" friction="1.0 0.005 0.0001"')
        x=x.replace('friction="0.3 0.005 0.0001"','friction="0.6 0.005 0.0001"')
    if 'unimass' in opts:
        x=re.sub(r'(<geom name="thigh_\w+_hull" type="mesh" mesh="thigh_\w+" mass=")0.01247', r'\g<1>0.03780', x)
        x=re.sub(r'(<body name="thigh_\w+"[^\n]*\n[^\n]*\n[^\n]*\n)\s*<geom type="box"[^\n]*\n', r'\1', x)
    return x
if __name__=="__main__":
  opts_list=[[],['soft'],['soft','tail8'],['soft','paw'],['soft','nohub'],['soft','unimass'],['soft','tail8','paw','nohub','unimass']]
  for opts in opts_list:
      x=make(opts)
      res=[R.drop_case(x,r,p,tries=1) for r,p in CASES]
      print('+'.join(opts) or 'base', sum(c['ok'] for c in res), [c['settled_up'] for c in res], flush=True)
