#!/usr/bin/python3
import subprocess
import datetime
import json
import os
import argparse
import sys
import math
import shutil
import glob

# --- LOAD CONFIG ---
# We look for config.json in the same directory as this script
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Critical Error: Config file not found at {CONFIG_PATH}")
    sys.exit(1)
except json.JSONDecodeError:
    print(f"Critical Error: Config file at {CONFIG_PATH} is not valid JSON")
    sys.exit(1)

# Extract settings from config
CAM_CONFIG = config.get('cameras', {})
SYSTEM_CONFIG = config.get('system', {})
WEBROOT = SYSTEM_CONFIG.get('webroot', '/tmp')

def run_ffmpeg_command(cmd_list, task_name):
    """
    Helper to run FFMPEG commands quietly unless they fail.
    """
    try:
        # Run process, capturing output so we can hide it on success or show it on failure
        result = subprocess.run(
            cmd_list, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        return True
    except subprocess.CalledProcessError as err:
        print(f"\n[!] Critical Error during: {task_name}")
        print(f"    Return Code: {err.returncode}")
def generate_timelapse(cam_name, duration, interval, resolution=None, suffix="", keep_raw=False, skip_video=False):
    # 1. Setup Constraints and Paths
    now = datetime.datetime.now()
    timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    
    # Logic update: If skipping video, we must keep raw files
    if skip_video:
        keep_raw = True
        print("[i] --skip-video flag detected: Forcing --keep-raw to True.")
    
    # Calculate estimates
    expected_images = math.ceil(duration / interval)
    expected_finish = now + datetime.timedelta(seconds=duration)

    # Define Directories based on requirements
    # Raw images: webroot/<camera_name>/raw_images/
    raw_dir = os.path.join(WEBROOT, cam_name, "raw_images")
    # Videos: webroot/videos/
    video_dir = os.path.join(WEBROOT, cam_name, "videos")

    # Ensure directories exist
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)

    # Define File Paths
    # We use a pattern with the timestamp so concurrent runs don't overwrite
    file_prefix = f"{cam_name}_{timestamp_str}"
    
    # Pattern for ffmpeg to write/read images (e.g., cam1_2023..._%04d.jpg)
    image_pattern = os.path.join(raw_dir, f"{file_prefix}_%04d.jpg")
    
    # Final video output
    final_video_path = os.path.join(video_dir, f"{file_prefix}{suffix}.mp4")

    # 2. Output Start Status
    print(f"[*] Starting Timelapse Capture for '{cam_name}'")
    print(f"    - Start Time:      {now.strftime('%H:%M:%S')}")
    print(f"    - Duration:        {duration} seconds")
    print(f"    - Interval:        Every {interval} seconds")
    print(f"    - Expected Images: ~{expected_images}")
    print(f"    - Expected Finish: {expected_finish.strftime('%H:%M:%S')}")
    print(f"    - Raw Storage:     {raw_dir}")

    # 3. Capture Images
    # We use the fps filter (1/interval) to pull frames periodically from the RTSP stream
    cmd_capture = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-rtsp_transport", "tcp",  # TCP is more stable for RTSP
        "-i", CAM_CONFIG[cam_name],
        "-vf", f"fps=1/{interval}", # Capture one frame every X seconds
        "-t", str(duration),        # Run for specific duration
        "-q:v", "2",                # High quality JPG (1-31, lower is better)
        image_pattern
    ]

    success = run_ffmpeg_command(cmd_capture, "Image Capture")
    if not success:
        return

    # 4. Stitch Images into Video (Only if not skipped)
    if not skip_video:
        print(f"[*] Capture complete. Stitching video at 30fps...")

        # We input the image pattern and output an MP4
        filter_complex = []
        
        # If resolution scaling is requested
        if resolution:
            filter_complex.append(f"scale={resolution}")
        
        # Standard format requirement ensures compatibility
        filter_complex.append("format=yuv420p")

        cmd_stitch = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-framerate", "30",         # Output framerate (as requested)
            "-i", image_pattern,        # Input image sequence
            "-c:v", "libx264",          # H.264 Encoder
            "-vf", ",".join(filter_complex),
            final_video_path
        ]

        success = run_ffmpeg_command(cmd_stitch, "Video Stitching")
        if not success:
            return

        print(f"[+] Video successfully created: {final_video_path}")
    else:
        print(f"[*] Capture complete. Video generation skipped.")

    # 5. Final Output & Cleanup
    
    if keep_raw:
        print(f"[i] Raw images preserved in: {raw_dir}")
    else:
        # Delete the specific images generated by this run
        # We look for files matching the prefix we created
        # Note: glob usage here ensures we only delete what we made
        files_to_remove = glob.glob(os.path.join(raw_dir, f"{file_prefix}_*.jpg"))
        for f in files_to_remove:
            try:
                os.remove(f)
            except OSError:
                pass # Best effort removal
        print("[i] Raw images deleted.") 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Records a timelapse from an RTSP camera stream.",
        epilog="Example: python3 timelapse.py --cam cam1 --duration 60 --interval 5 --keep-raw"
    )
    
    parser.add_argument(
        "--cam", 
        required=True, 
        help="Camera name as defined in config.json (e.g., 'front_door')"
    )
    parser.add_argument(
        "--duration", 
        type=int, 
        required=True, 
        help="Total duration to capture in seconds."
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        required=True, 
        help="Interval in seconds between image captures (e.g., 5 means one photo every 5 seconds)."
    )
    parser.add_argument(
        "--res", 
        type=str, 
        default=None, 
        help="Optional output resolution (e.g., 1280:720). Defaults to source resolution."
    )
    parser.add_argument(
        "--suffix", 
        type=str, 
        default="", 
        help="String to append to the final filename (e.g., '_morning')."
    )
    parser.add_argument(
        "--keep-raw", 
        action="store_true", 
        help="If set, raw JPG images will NOT be deleted after video creation."
    )
    parser.add_argument(
        "--skip-video", 
        action="store_true", 
        help="If set, only captures images. Skips video stitching and forces --keep-raw to True."
    )

    args = parser.parse_args()

    # Validate Camera Exists in Config
    if args.cam not in CAM_CONFIG:
        print(f"Error: Camera '{args.cam}' not found in config.json.")
        print(f"Available cameras: {', '.join(CAM_CONFIG.keys())}")
        sys.exit(1)

    try:
        generate_timelapse(
            cam_name=args.cam,
            duration=args.duration,
            interval=args.interval,
            resolution=args.res,
            suffix=args.suffix,
            keep_raw=args.keep_raw,
            skip_video=args.skip_video
        )
    except KeyboardInterrupt:
        print("\n[!] Script interrupted by user.")
        sys.exit(0)
