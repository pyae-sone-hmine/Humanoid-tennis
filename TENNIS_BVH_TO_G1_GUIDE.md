# Tennis BVH to Unitree G1 Conversion Guide

This guide provides step-by-step instructions to convert tennis motion capture (BVH) files to Unitree G1 robot motions using the General Motion Retargeting (GMR) system.

## Prerequisites

- Linux system (tested on Ubuntu)
- Internet connection for downloading dependencies
- Tennis BVH files (from Tennis-MoCap dataset)

## Step 1: Install Miniconda

```bash
# Download Miniconda installer
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh

# Install Miniconda
bash miniconda.sh -b -p $HOME/miniconda3

# Initialize conda
$HOME/miniconda3/bin/conda init bash

# Accept terms of service
source $HOME/miniconda3/etc/profile.d/conda.sh
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r
```

## Step 2: Create Python Environment

```bash
# Create conda environment with Python 3.10 (required by GMR)
source $HOME/miniconda3/etc/profile.d/conda.sh
conda create -n tennis_gmr python=3.10 -y

# Activate environment
conda activate tennis_gmr
```

## Step 3: Install GMR Package

```bash
# Navigate to GMR directory
cd /path/to/your/humanoid_tennis/GMR

# Install GMR package in development mode
pip install -e .
```

This will install all required dependencies including:
- numpy, scipy, torch
- mujoco (for robot simulation)
- rich, tqdm (for progress display)
- smplx (for human body models)
- And other motion retargeting dependencies

## Step 4: Directory Structure

Ensure your directory structure looks like this:
```
humanoid_tennis/
├── GMR/                           # General Motion Retargeting package
├── Tennis-MoCap-main/
│   └── data/
│       ├── cferrero_Servicio.bvh
│       ├── jduribe_Servicio.bvh
│       ├── jsgiraldo_Derecha.bvh
│       └── ... (other tennis BVH files)
├── batch_tennis_converter.py
├── inspect_motion.py
└── tennis_motions/               # Output directory (created automatically)
```

## Step 5: Convert Single Tennis Motion

The original `bvh_to_robot.py` script works perfectly with our tennis-specific patches:

```bash
# Activate environment
source $HOME/miniconda3/etc/profile.d/conda.sh
conda activate tennis_gmr

# Navigate to project directory
cd /path/to/your/humanoid_tennis

# Convert single BVH file (headless version - no visualization)
python bvh_to_robot_headless.py \
    --bvh_file Tennis-MoCap-main/data/cferrero_Servicio.bvh \
    --save_path tennis_motions/cferrero_serve_g1.pkl

# Or with visualization (if you have a display)
python bvh_to_robot_tennis.py \
    --bvh_file Tennis-MoCap-main/data/cferrero_Servicio.bvh \
    --save_path tennis_motions/cferrero_serve_g1.pkl
```


### Expected Output
```
Converting Tennis-MoCap-main/data/cferrero_Servicio.bvh to Unitree G1 motion...
Converting tennis BVH to LAFAN1: Tennis-MoCap-main/data/cferrero_Servicio.bvh
Reading tennis BVH file: Tennis-MoCap-main/data/cferrero_Servicio.bvh
Original bones: ['Hips', 'Chest', 'Neck', 'Head', 'LeftCollar', 'LeftShoulder', ...]
Mapped bones: ['Hips', 'Spine2', 'Neck', 'Head', 'LeftCollar', 'LeftArm', ...]
Converted 2999 frames, human height: -0.24m
...
Successfully converted and saved to: tennis_motions/cferrero_serve_demo.pkl
```

## Step 6: Batch Conversion

### Convert All Serve Motions
```bash
python batch_tennis_converter.py \
    --input_dir Tennis-MoCap-main/data \
    --output_dir tennis_motions \
    --pattern "*Servicio*.bvh"
```

### Convert by Stroke Type
```bash
python batch_tennis_converter.py \
    --input_dir Tennis-MoCap-main/data \
    --output_dir tennis_motions \
    --organize_by stroke
```

This creates organized directories:
```
tennis_motions/
├── servicio/          # All serve motions
├── derecha/           # All forehand motions
├── reves/             # All backhand motions
├── remate/            # All smash motions
├── vderecha/          # All volley forehand motions
└── vreves/            # All volley backhand motions
```

### Convert by Player
```bash
python batch_tennis_converter.py \
    --input_dir Tennis-MoCap-main/data \
    --output_dir tennis_motions \
    --organize_by player
```

## Step 7: Inspect Converted Motions

```bash
# Inspect motion file contents
python inspect_motion.py tennis_motions/cferrero_serve_demo.pkl
```

### Expected Output
```
Inspecting motion file: tennis_motions/cferrero_serve_demo.pkl

=== Motion Data Structure ===
fps: 30
root_pos: shape=(2999, 3), dtype=float64
root_rot: shape=(2999, 4), dtype=float64
dof_pos: shape=(2999, 29), dtype=float64

=== Motion Summary ===
Duration: 100.0 seconds
Frames: 2999
FPS: 30
Robot DOF: 29

=== Root Position (pelvis) ===
X range: [-0.246, -0.010] meters
Y range: [-0.166, 0.119] meters
Z range: [-0.172, 0.097] meters
```

## Step 8: Understanding the Output

### Motion Data Structure
Each converted `.pkl` file contains:
- **`fps`**: Frame rate (30 FPS)
- **`root_pos`**: Pelvis position (X, Y, Z) for each frame
- **`root_rot`**: Pelvis orientation (quaternion) for each frame
- **`dof_pos`**: All 29 joint angles for each frame
- **`local_body_pos`**: Local body positions (None for tennis data)
- **`link_body_list`**: Body link names (None for tennis data)

### Unitree G1 Joint Mapping
The 29 DOF correspond to:
- **DOF 0-5**: Pelvis (position + orientation)
- **DOF 6-11**: Left leg (hip pitch/roll/yaw, knee, ankle pitch/roll)
- **DOF 12-17**: Right leg (hip pitch/roll/yaw, knee, ankle pitch/roll)
- **DOF 18-20**: Waist (yaw, roll, pitch)
- **DOF 21-27**: Left arm (shoulder pitch/roll/yaw, elbow, wrist roll/pitch/yaw)
- **DOF 28-34**: Right arm (shoulder pitch/roll/yaw, elbow, wrist roll/pitch/yaw)

## Step 9: Bone Mapping Reference

### Tennis BVH → LAFAN1 Mapping
```
Tennis Bone Name    → LAFAN1 Bone Name
Hips               → Hips
Chest              → Spine2
Neck               → Neck
Head               → Head
LeftCollar         → LeftCollar
LeftShoulder       → LeftArm
LeftElbow          → LeftForeArm
LeftWrist          → LeftHand
RightCollar        → RightCollar
RightShoulder      → RightArm
RightElbow         → RightForeArm
RightWrist         → RightHand
LeftHip            → LeftUpLeg
LeftKnee           → LeftLeg
LeftAnkle          → LeftFoot
RightHip           → RightUpLeg
RightKnee          → RightLeg
RightAnkle         → RightFoot
```

## Step 10: Troubleshooting

### Common Issues

1. **"conda: command not found"**
   ```bash
   source $HOME/miniconda3/etc/profile.d/conda.sh
   ```

2. **"Python 2.7" instead of Python 3**
   ```bash
   conda activate tennis_gmr
   python --version  # Should show Python 3.10.x
   ```

3. **"ValueError: could not convert string to float"**
   - This is handled by the custom tennis BVH parser
   - Make sure you're using `tennis_bvh_to_lafan1_converter.py`

4. **"ModuleNotFoundError: No module named 'general_motion_retargeting'"**
   ```bash
   cd GMR
   pip install -e .
   ```

5. **CUDA/GPU Issues**
   - The system works on CPU
   - GPU acceleration is optional for faster processing

### Performance Notes
- Single motion conversion: ~1-2 minutes per file
- Batch conversion: Progress bar shows estimated time
- Memory usage: ~1-2 GB per conversion
- Output file size: ~800KB-1MB per motion

## Step 11: Using Converted Motions

### Loading Motion Data
```python
import pickle
import numpy as np

# Load converted motion
with open('tennis_motions/cferrero_serve_demo.pkl', 'rb') as f:
    motion_data = pickle.load(f)

# Access motion components
root_positions = motion_data['root_pos']      # Shape: (frames, 3)
root_rotations = motion_data['root_rot']      # Shape: (frames, 4)
joint_angles = motion_data['dof_pos']         # Shape: (frames, 29)
fps = motion_data['fps']                      # 30

# Example: Get first frame pose
first_frame_pos = root_positions[0]           # [x, y, z]
first_frame_rot = root_rotations[0]           # [w, x, y, z] quaternion
first_frame_joints = joint_angles[0]          # 29 joint angles
```

### Robot Control Integration
The converted motion data can be integrated with Unitree G1 control systems:
1. Load the `.pkl` file
2. Extract joint angles for each frame
3. Send commands to robot at 30 FPS
4. Monitor execution and adjust timing as needed

## Step 12: Advanced Usage

### Custom Bone Mapping
Edit `tennis_bvh_to_lafan1_converter.py` and modify the `map_tennis_bones_to_lafan1()` function to adjust bone mappings for different BVH formats.

### Different Robot Models
To retarget to other robots supported by GMR:
```bash
python tennis_bvh_to_lafan1_converter.py \
    --bvh_file Tennis-MoCap-main/data/cferrero_Servicio.bvh \
    --robot unitree_h1  # or other supported robots
```

### Motion Filtering
Add motion smoothing or filtering by modifying the conversion pipeline in the converter script.

## Summary

This pipeline successfully converts tennis motion capture data to executable Unitree G1 robot motions. The key components are:

1. **Custom BVH Parser**: Handles tennis-specific bone naming and formatting
2. **Bone Mapping**: Maps tennis skeleton to LAFAN1 format
3. **Motion Retargeting**: Uses GMR's IK system for robot-specific conversion
4. **Batch Processing**: Efficiently converts multiple motions
5. **Output Format**: Structured pickle files ready for robot execution

The converted motions preserve the essential characteristics of tennis strokes while adapting them to the robot's kinematic constraints and capabilities.
