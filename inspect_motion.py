#!/usr/bin/env python3
"""
Inspect converted tennis motion data
"""

import pickle
import numpy as np

def inspect_motion_file(pkl_file):
    """Inspect the contents of a converted motion file"""
    print(f"Inspecting motion file: {pkl_file}")
    
    with open(pkl_file, 'rb') as f:
        motion_data = pickle.load(f)
    
    print("\n=== Motion Data Structure ===")
    for key, value in motion_data.items():
        if isinstance(value, np.ndarray):
            print(f"{key}: shape={value.shape}, dtype={value.dtype}")
            if key in ['root_pos', 'root_rot', 'dof_pos']:
                print(f"  - Range: [{value.min():.3f}, {value.max():.3f}]")
        else:
            print(f"{key}: {value}")
    
    print(f"\n=== Motion Summary ===")
    print(f"Duration: {motion_data['root_pos'].shape[0] / motion_data['fps']:.1f} seconds")
    print(f"Frames: {motion_data['root_pos'].shape[0]}")
    print(f"FPS: {motion_data['fps']}")
    print(f"Robot DOF: {motion_data['dof_pos'].shape[1]}")
    
    print(f"\n=== Root Position (pelvis) ===")
    root_pos = motion_data['root_pos']
    print(f"X range: [{root_pos[:, 0].min():.3f}, {root_pos[:, 0].max():.3f}] meters")
    print(f"Y range: [{root_pos[:, 1].min():.3f}, {root_pos[:, 1].max():.3f}] meters") 
    print(f"Z range: [{root_pos[:, 2].min():.3f}, {root_pos[:, 2].max():.3f}] meters")
    
    print(f"\n=== Joint Angles (first 5 DOF) ===")
    dof_pos = motion_data['dof_pos']
    for i in range(min(5, dof_pos.shape[1])):
        print(f"DOF {i}: range [{dof_pos[:, i].min():.3f}, {dof_pos[:, i].max():.3f}] radians")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        inspect_motion_file(sys.argv[1])
    else:
        inspect_motion_file("tennis_motions/cferrero_serve_demo.pkl")


