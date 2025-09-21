#!/usr/bin/env python3
"""
Batch Tennis BVH to Unitree G1 Converter
Converts all tennis BVH files to Unitree G1 motions
"""

import os
import glob
import argparse
import subprocess
from tqdm import tqdm


def batch_convert_tennis_motions(input_dir, output_dir="tennis_motions", pattern="*.bvh"):
    """
    Convert all tennis BVH files in a directory to Unitree G1 motions
    
    Args:
        input_dir: Directory containing tennis BVH files
        output_dir: Directory to save converted motions
        pattern: File pattern to match (default: "*.bvh")
    """
    
    # Find all BVH files
    bvh_files = glob.glob(os.path.join(input_dir, pattern))
    
    if not bvh_files:
        print(f"No BVH files found in {input_dir} with pattern {pattern}")
        return
    
    print(f"Found {len(bvh_files)} BVH files to convert")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    successful_conversions = 0
    failed_conversions = 0
    
    # Process each file
    for bvh_file in tqdm(bvh_files, desc="Converting tennis motions"):
        try:
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(bvh_file))[0]
            output_file = os.path.join(output_dir, f"{base_name}_g1.pkl")
            
            # Skip if already converted
            if os.path.exists(output_file):
                print(f"Skipping {bvh_file} - already converted")
                continue
            
            print(f"\nConverting: {bvh_file}")
            
            # Convert using the proper GMR script
            cmd = [
                "python", "bvh_to_robot_headless.py",
                "--bvh_file", bvh_file,
                "--save_path", output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                successful_conversions += 1
            else:
                print(f"Failed to convert {bvh_file}: {result.stderr}")
                failed_conversions += 1
            
        except Exception as e:
            print(f"Failed to convert {bvh_file}: {e}")
            failed_conversions += 1
    
    print(f"\nBatch conversion complete!")
    print(f"Successful conversions: {successful_conversions}")
    print(f"Failed conversions: {failed_conversions}")
    print(f"Output directory: {output_dir}")


def convert_by_stroke_type(input_dir, output_dir="tennis_motions"):
    """
    Convert tennis motions organized by stroke type
    """
    stroke_types = ["Servicio", "Derecha", "Reves", "Remate", "VDerecha", "VReves"]
    
    for stroke in stroke_types:
        print(f"\n=== Converting {stroke} strokes ===")
        pattern = f"*{stroke}*.bvh"
        stroke_output_dir = os.path.join(output_dir, stroke.lower())
        batch_convert_tennis_motions(input_dir, stroke_output_dir, pattern)


def convert_by_player(input_dir, output_dir="tennis_motions"):
    """
    Convert tennis motions organized by player
    """
    # Get all unique player names from BVH files
    bvh_files = glob.glob(os.path.join(input_dir, "*.bvh"))
    players = set()
    
    for bvh_file in bvh_files:
        filename = os.path.basename(bvh_file)
        if '_' in filename:
            player = filename.split('_')[0]
            players.add(player)
    
    print(f"Found {len(players)} players: {sorted(players)}")
    
    for player in sorted(players):
        print(f"\n=== Converting {player} motions ===")
        pattern = f"{player}_*.bvh"
        player_output_dir = os.path.join(output_dir, player.lower())
        batch_convert_tennis_motions(input_dir, player_output_dir, pattern)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch convert tennis BVH files to Unitree G1 motions")
    parser.add_argument("--input_dir", required=True, help="Directory containing tennis BVH files")
    parser.add_argument("--output_dir", default="tennis_motions", help="Output directory for converted motions")
    parser.add_argument("--pattern", default="*.bvh", help="File pattern to match")
    parser.add_argument("--organize_by", choices=["none", "stroke", "player"], default="none", 
                       help="How to organize output files")
    
    args = parser.parse_args()
    
    if args.organize_by == "stroke":
        convert_by_stroke_type(args.input_dir, args.output_dir)
    elif args.organize_by == "player":
        convert_by_player(args.input_dir, args.output_dir)
    else:
        batch_convert_tennis_motions(args.input_dir, args.output_dir, args.pattern)
