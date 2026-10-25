#!/bin/bash
# final evaluations (test seeds 0-11, mu 0.3/0.4/0.6, rows + diag, K1 + K2, flat x6)
cd "$(dirname "$0")"
O=../out
M='{"ski":0.005,"track_add":0.025}'
python3 batch.py baseline BASE 12 2>&1 | grep -v Warn | tail -15 > $O/log_BASE.txt
python3 batch.py $O/spec_RT.json RT 12 2>&1 | grep -v Warn | tail -15 > $O/log_RT.txt
python3 batch.py $O/spec_RT8.json RT8 12 2>&1 | grep -v Warn | tail -15 > $O/log_RT8.txt
python3 batch.py $O/spec_WALK.json WALK 12 2>&1 | grep -v Warn | tail -15 > $O/log_WALK.txt
python3 batch.py $O/spec_MECH.json MECH 12 K1,K2 0.3,0.4,0.6 rows,diag "$M" 2>&1 | grep -v Warn | tail -15 > $O/log_MECH.txt
python3 batch.py $O/spec_MECH.json MECH_T 12 K1,K2 0.3,0.4,0.6 rows,diag '{"track_add":0.025}' 2>&1 | grep -v Warn | tail -15 > $O/log_MECH_T.txt
python3 batch.py $O/spec_MECH.json MECH_S 12 K2 0.3,0.4,0.6 rows,diag '{"ski":0.005}' 2>&1 | grep -v Warn | tail -9 > $O/log_MECH_S.txt
python3 batch.py baseline BASE_MECH 12 K2 0.3,0.4,0.6 rows,diag "$M" 2>&1 | grep -v Warn | tail -9 > $O/log_BASE_MECH.txt
python3 batch.py $O/spec_RT.json RT_MECH 12 K2 0.3,0.4,0.6 rows,diag "$M" 2>&1 | grep -v Warn | tail -9 > $O/log_RT_MECH.txt
python3 batch.py $O/spec_MECH.json MECH_SHIN20 12 K1,K2 0.3,0.4,0.6 rows,diag '{"ski":0.005,"track_add":0.025,"shin_ext":0.020}' 2>&1 | grep -v Warn | tail -15 > $O/log_MECH_SHIN20.txt
TAU=0.16 python3 batch.py $O/spec_MECH.json MECH_tau016 12 K1,K2 0.3,0.4,0.6 rows,diag "$M" 2>&1 | grep -v Warn | tail -15 > $O/log_MECH_tau016.txt
TAU=0.16 python3 batch.py baseline BASE_tau016 12 K1,K2 0.4 rows,diag 2>&1 | grep -v Warn | tail -8 > $O/log_BASE_tau016.txt
python3 tracks.py 2>&1 | grep -v Warn > $O/log_tracks.txt
echo ALLDONE
