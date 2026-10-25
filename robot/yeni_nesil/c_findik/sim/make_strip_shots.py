"""Shot list for the posecheck animation strips (fixed camera per clip)."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
CLIPS = {
 # name: (camera, times)
 "idle":   ({"azimuth": 30, "elevation": 12, "target": [0, 0, 55], "distance": 1.1}, [0.0, 1.0, 1.36, 2.0, 3.3, 4.0]),
 "talk":   ({"azimuth": 20, "elevation": 10, "target": [0, 0, 55], "distance": 1.1}, [0.17, 0.37, 1.0, 1.8, 3.83, 4.9]),
 "happy":  ({"azimuth": -35, "elevation": 14, "target": [5, -5, 50], "distance": 1.25}, [0.0, 0.6, 1.0, 1.2, 1.4, 2.4, 3.0, 3.3, 3.6, 3.95]),
 "walk":   ({"azimuth": 75, "elevation": 14, "target": [0, -360, 50], "distance": 5.0}, [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 6.95]),
 "turn":   ({"azimuth": 25, "elevation": 30, "target": [-2, -12, 45], "distance": 1.3}, [0.0, 0.8, 1.4, 2.0, 2.6, 3.2, 3.9, 4.4, 4.97]),
 # close follow-cam for walk (no target = camera follows the robot at a fixed angle/distance; the grid shows the motion)
 "walk_follow": ({"azimuth": 65, "elevation": 10, "distance": 1.25}, [0.0, 0.8, 1.6, 3.0, 5.0, 6.2, 6.95]),
 "sleep":  ({"azimuth": 35, "elevation": 12, "target": [0, -10, 45], "distance": 1.15}, [0.0, 0.8, 1.6, 2.3, 2.5, 3.0, 3.95]),
 "fall_recover":  ({"azimuth": 0, "elevation": 14, "target": [30, -25, 45], "distance": 1.6}, [1.4, 1.75, 2.05, 2.25, 2.4, 2.6, 2.8, 3.0, 3.2, 3.45, 4.2, 5.5]),
 "fall_back_help":({"azimuth": 80, "elevation": 14, "target": [0, 25, 45], "distance": 1.6}, [1.4, 1.65, 1.9, 2.1, 2.4, 3.0, 3.6, 4.3, 5.0, 5.5]),
}
ALIAS = {"walk_follow": "walk"}
shots = []; follow = []
for clip, (cam, ts) in CLIPS.items():
    for i, t in enumerate(ts):
        s = dict(cam); s.update({"name": f"{clip}_{i:02d}", "anim": ALIAS.get(clip, clip), "t": t})
        (follow if clip == "walk_follow" else shots).append(s)
json.dump({"width": 800, "height": 600, "shots": shots}, open(os.path.join(HERE, "strip_shots.json"), "w"), indent=0)
# walk_follow is rendered from the wrapped-base package made by make_follow_pkg.py (grid and shadow stay under the robot)
json.dump({"width": 800, "height": 600, "shots": follow}, open(os.path.join(HERE, "strip_follow.json"), "w"), indent=0)
json.dump({k: v[1] for k, v in CLIPS.items()}, open(os.path.join(HERE, "strip_times.json"), "w"))
print(len(shots), "shots")
