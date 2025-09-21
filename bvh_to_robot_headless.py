#!/usr/bin/env python3
"""
Headless BVH to Robot Converter (No Visualization)
Patched version of bvh_to_robot.py that works with tennis BVH files
"""

import argparse
import pathlib
import time
import re
import numpy as np
from scipy.spatial.transform import Rotation as R
from general_motion_retargeting import GeneralMotionRetargeting as GMR
from general_motion_retargeting.utils.lafan_vendor import utils
from rich import print
from tqdm import tqdm
import os


def read_tennis_bvh(filename):
    """Custom BVH reader that handles tennis files with trailing spaces"""
    f = open(filename, "r")
    
    i = 0
    active = -1
    end_site = False
    
    names = []
    orients = np.array([]).reshape((0, 4))
    offsets = np.array([]).reshape((0, 3))
    parents = np.array([], dtype=int)
    
    # Parse the file, line by line
    for line in f:
        if "HIERARCHY" in line: continue
        if "MOTION" in line: continue
        
        rmatch = re.match(r"ROOT (\w+)", line)
        if rmatch:
            names.append(rmatch.group(1))
            offsets = np.append(offsets, np.array([[0, 0, 0]]), axis=0)
            orients = np.append(orients, np.array([[1, 0, 0, 0]]), axis=0)
            parents = np.append(parents, active)
            active = (len(parents) - 1)
            continue
        
        if "{" in line: continue
        
        if "}" in line:
            if end_site:
                end_site = False
            else:
                active = parents[active]
            continue
        
        offmatch = re.match(r"\s*OFFSET\s+([\-\d\.e]+)\s+([\-\d\.e]+)\s+([\-\d\.e]+)", line)
        if offmatch:
            if not end_site:
                offsets[active] = np.array([list(map(float, offmatch.groups()))])
            continue
        
        chanmatch = re.match(r"\s*CHANNELS\s+(\d+)", line)
        if chanmatch:
            channels = int(chanmatch.group(1))
            continue
        
        jmatch = re.match("\s*JOINT\s+(\w+)", line)
        if jmatch:
            names.append(jmatch.group(1))
            offsets = np.append(offsets, np.array([[0, 0, 0]]), axis=0)
            orients = np.append(orients, np.array([[1, 0, 0, 0]]), axis=0)
            parents = np.append(parents, active)
            active = (len(parents) - 1)
            continue
        
        if "End Site" in line:
            end_site = True
            continue
        
        fmatch = re.match("\s*Frames:\s+(\d+)", line)
        if fmatch:
            fnum = int(fmatch.group(1))
            positions = offsets[np.newaxis].repeat(fnum, axis=0)
            rotations = np.zeros((fnum, len(orients), 3))
            continue
        
        fmatch = re.match("\s*Frame Time:\s+([\d\.]+)", line)
        if fmatch:
            frametime = float(fmatch.group(1))
            continue
        
        # Parse motion data lines - FIXED: handle trailing spaces
        if line.strip() and not line.startswith(('HIERARCHY', 'MOTION', 'ROOT', 'JOINT', 'End Site', 'OFFSET', 'CHANNELS', 'Frames:', 'Frame Time:')):
            # Clean the line and split by whitespace
            dmatch = line.strip().split()
            if dmatch and all(re.match(r'^-?\d+\.?\d*$', val) for val in dmatch):
                try:
                    data_block = np.array(list(map(float, dmatch)))
                    N = len(parents)
                    fi = i
                    if channels == 3:
                        positions[fi, 0:1] = data_block[0:3]
                        rotations[fi, :] = data_block[3:].reshape(N, 3)
                    elif channels == 6:
                        data_block = data_block.reshape(N, 6)
                        positions[fi, :] = data_block[:, 0:3]
                        rotations[fi, :] = data_block[:, 3:6]
                    elif channels == 9:
                        positions[fi, 0] = data_block[0:3]
                        data_block = data_block[3:].reshape(N - 1, 9)
                        rotations[fi, 1:] = data_block[:, 3:6]
                        positions[fi, 1:] += data_block[:, 0:3] * data_block[:, 6:9]
                    else:
                        raise Exception("Too many channels! %i" % channels)
                    
                    i += 1
                except Exception as e:
                    print(f"Error parsing line {i}: {e}")
                    continue
    
    f.close()
    
    # Convert Euler angles to quaternions
    rotations = utils.euler_to_quat(np.radians(rotations), order='zyx')
    rotations = utils.remove_quat_discontinuities(rotations)
    
    class Anim:
        def __init__(self, quats, pos, offsets, parents, bones):
            self.quats = quats
            self.pos = pos
            self.offsets = offsets
            self.parents = parents
            self.bones = bones
    
    return Anim(rotations, positions, offsets, parents, names)


def map_tennis_bones_to_lafan1(bone_names):
    """Map tennis BVH bone names to LAFAN1 bone names"""
    bone_mapping = {
        'Hips': 'Hips',
        'Chest': 'Spine2',
        'Neck': 'Neck',
        'Head': 'Head',
        'LeftCollar': 'LeftCollar',
        'LeftShoulder': 'LeftArm',
        'LeftElbow': 'LeftForeArm', 
        'LeftWrist': 'LeftHand',
        'RightCollar': 'RightCollar',
        'RightShoulder': 'RightArm',
        'RightElbow': 'RightForeArm',
        'RightWrist': 'RightHand',
        'LeftHip': 'LeftUpLeg',
        'LeftKnee': 'LeftLeg',
        'LeftAnkle': 'LeftFoot',
        'RightHip': 'RightUpLeg', 
        'RightKnee': 'RightLeg',
        'RightAnkle': 'RightFoot'
    }
    
    mapped_names = []
    for bone in bone_names:
        if bone in bone_mapping:
            mapped_names.append(bone_mapping[bone])
        else:
            mapped_names.append(bone)
    
    return mapped_names


def load_tennis_lafan1_file(bvh_file):
    """Load tennis BVH file and convert to LAFAN1 format"""
    print(f"Converting tennis BVH to LAFAN1: {bvh_file}")
    
    # Read the tennis BVH file
    data = read_tennis_bvh(bvh_file)
    
    # Map bone names to LAFAN1 format
    mapped_bones = map_tennis_bones_to_lafan1(data.bones)
    
    print(f"Original bones: {data.bones}")
    print(f"Mapped bones: {mapped_bones}")
    
    # Create a new data structure with mapped bone names
    class TennisAnim:
        def __init__(self, quats, pos, offsets, parents, bones):
            self.quats = quats
            self.pos = pos
            self.offsets = offsets
            self.parents = parents
            self.bones = bones
    
    tennis_data = TennisAnim(data.quats, data.pos, data.offsets, data.parents, mapped_bones)
    
    # Perform forward kinematics
    global_data = utils.quat_fk(tennis_data.quats, tennis_data.pos, tennis_data.parents)

    # Apply coordinate system transformation
    rotation_matrix = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]])
    rotation_quat = R.from_matrix(rotation_matrix).as_quat(scalar_first=True)

    frames = []
    for frame in range(tennis_data.pos.shape[0]):
        result = {}
        for i, bone in enumerate(tennis_data.bones):
            orientation = utils.quat_mul(rotation_quat, global_data[0][frame, i])
            position = global_data[1][frame, i] @ rotation_matrix.T / 100  # cm to m
            result[bone] = (position, orientation)

        # Add modified foot pose (required for LAFAN1)
        if "LeftFoot" in result and "LeftToe" in result:
            result["LeftFootMod"] = (result["LeftFoot"][0], result["LeftToe"][1])
        else:
            result["LeftFootMod"] = (result.get("LeftFoot", (np.array([0, 0, 0]), np.array([1, 0, 0, 0])))[0], 
                                   result.get("LeftFoot", (np.array([0, 0, 0]), np.array([1, 0, 0, 0])))[1])
            
        if "RightFoot" in result and "RightToe" in result:
            result["RightFootMod"] = (result["RightFoot"][0], result["RightToe"][1])
        else:
            result["RightFootMod"] = (result.get("RightFoot", (np.array([0, 0, 0]), np.array([1, 0, 0, 0])))[0], 
                                    result.get("RightFoot", (np.array([0, 0, 0]), np.array([1, 0, 0, 0])))[1])
        
        frames.append(result)
    
    # Calculate human height
    if "Head" in result and "LeftFootMod" in result and "RightFootMod" in result:
        human_height = result["Head"][0][2] - min(result["LeftFootMod"][0][2], result["RightFootMod"][0][2])
    else:
        human_height = 1.75  # Default height
    
    print(f"Converted {len(frames)} frames, human height: {human_height:.2f}m")
    
    return frames, human_height


if __name__ == "__main__":
    
    HERE = pathlib.Path(__file__).parent

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bvh_file",
        help="BVH motion file to load.",
        required=True,
        type=str,
    )
    
    parser.add_argument(
        "--robot",
        choices=["unitree_g1", "unitree_g1_with_hands", "booster_t1", "stanford_toddy", "fourier_n1", "engineai_pm01"],
        default="unitree_g1",
    )

    parser.add_argument(
        "--save_path",
        default=None,
        help="Path to save the robot motion.",
    )
    
    args = parser.parse_args()
    
    if args.save_path is not None:
        save_dir = os.path.dirname(args.save_path)
        if save_dir:  # Only create directory if it's not empty
            os.makedirs(save_dir, exist_ok=True)
        qpos_list = []

    # Load tennis BVH trajectory - MODIFIED: use tennis-specific loader
    lafan1_data_frames, actual_human_height = load_tennis_lafan1_file(args.bvh_file)
    
    # Initialize the retargeting system
    retargeter = GMR(
        src_human="bvh",
        tgt_robot=args.robot,
        actual_human_height=actual_human_height,
    )

    motion_fps = 30
    
    print(f"mocap_frame_rate: {motion_fps}")
    
    # Create tqdm progress bar for the total number of frames
    pbar = tqdm(total=len(lafan1_data_frames), desc="Retargeting")
    
    # Process all frames
    for i, smplx_data in enumerate(lafan1_data_frames):
        # Update progress bar
        pbar.update(1)

        # retarget
        qpos = retargeter.retarget(smplx_data)

        if args.save_path is not None:
            qpos_list.append(qpos)
    
    if args.save_path is not None:
        import pickle
        root_pos = np.array([qpos[:3] for qpos in qpos_list])
        # save from wxyz to xyzw
        root_rot = np.array([qpos[3:7][[1,2,3,0]] for qpos in qpos_list])
        dof_pos = np.array([qpos[7:] for qpos in qpos_list])
        local_body_pos = None
        body_names = None
        
        motion_data = {
            "fps": motion_fps,
            "root_pos": root_pos,
            "root_rot": root_rot,
            "dof_pos": dof_pos,
            "local_body_pos": local_body_pos,
            "link_body_list": body_names,
        }
        with open(args.save_path, "wb") as f:
            pickle.dump(motion_data, f)
        print(f"Saved to {args.save_path}")

    # Close progress bar
    pbar.close()


