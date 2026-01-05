#!/usr/bin/python3
import subprocess
import datetime
import json
import os
import argparse
import sys

# --- LOAD CONFIG ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Critical Error: Config file not found at {CONFIG_PATH}")
    sys.exit(1)

# Extract settings
CAM_CONFIG = config['cameras']
OUTPUT_ROOT = config['system']['webroot']

def record_stream(cam_name, duration, speed=1.0, resolution=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    cam_dir = os.path.join(OUTPUT_ROOT, cam_name)
    raw_file = os.path.join(cam_dir, f"{timestamp}_raw.mp4")
    final_file = os.path.join(cam_dir, f"{timestamp}.mp4")

    # ensure directory exists
    os.makedirs(cam_dir, exist_ok=True)

    print(f"[*] Starting recording for {cam_name} ({duration}s)...")

    # 1. Capture stream to raw file (copy codec = low CPU usage)
    # Using TCP transport is more reliable for RTSP over WiFi/Ethernet
    cmd_capture = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-rtsp_transport", "tcp",
        "-i", CAM_CONFIG[cam_name],
        "-t", str(duration),
        "-c", "copy",
        raw_file
    ]

    try:
        subprocess.run(cmd_capture, check=True)
    except subprocess.CalledProcessError:
        print(f"[!] Error capturing stream from {cam_name}")
        return

    # 2. Process Video (Speed up / Resize)
    # If speed is 1.0 and no res change, just rename raw file
    if speed == 1.0 and resolution is None:
        os.rename(raw_file, final_file)
        print(f"[+] Saved: {final_file}")
        return

    print("[*] Processing video...")
    
    filter_chains = []
    
    # Speed Up Logic (setpts filter)
    if speed != 1.0:
        pts_factor = 1.0 / speed
        filter_chains.append(f"setpts={pts_factor}*PTS")
    
    # Resolution Logic (scale filter)
    if resolution:
        filter_chains.append(f"scale={resolution}")

    cmd_process = ["ffmpeg", "-y", "-i", raw_file, "-filter:v", ",".join(filter_chains)]
    
    # Remove audio if speeding up (audio sounds weird sped up)
    if speed != 1.0:
        cmd_process.append("-an")

    cmd_process.append(final_file)

    try:
        subprocess.run(cmd_process, check=True)
        os.remove(raw_file) # Delete raw file to save space
        print(f"[+] Processed & Saved: {final_file}")
    except subprocess.CalledProcessError:
        print("[!] Error processing video")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cam", required=True, help="Camera name (cam1/cam2)")
    parser.add_argument("--duration", type=int, required=True, help="Duration in seconds")
    parser.add_argument("--speed", type=float, default=1.0, help="Speed multiplier (e.g. 2.0)")
    parser.add_argument("--res", type=str, default=None, help="Resolution (e.g. 1280:720)")
    
    args = parser.parse_args()
    
    if args.cam not in CAM_CONFIG:
        print("Invalid camera name.")
        sys.exit(1)

    record_stream(args.cam, args.duration, args.speed, args.res)
