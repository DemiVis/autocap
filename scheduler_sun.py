#!/usr/bin/python3
import argparse
import json
import subprocess
import time
import datetime
import os
import sys
import pytz
from suntime import Sun

# --- LOAD CONFIG ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Critical Error: Config file not found at {CONFIG_PATH}")
    sys.exit(1)

# Set defaults from JSON
# You can override these via command line arguments
DEFAULT_LAT = config['location']['latitude']
DEFAULT_LONG = config['location']['longitude']
TIMEZONE_NAME = config['location']['timezone']

# We need to pass the location of record.py 
# Assuming record.py is in the SAME folder as this script
RECORD_SCRIPT = os.path.join(os.path.dirname(__file__), "record.py")

def get_args():
    parser = argparse.ArgumentParser(description="Solar Event Scheduler")
    parser.add_argument("--cam", required=True, help="Camera name (e.g., cam1)")
    parser.add_argument("--mode", required=True, choices=['sunrise', 'sunset'], help="Event type")
    parser.add_argument("--start_offset", type=int, default=-20, help="Minutes relative to event to START (negative = before)")
    parser.add_argument("--end_offset", type=int, default=30, help="Minutes relative to event to END")
    parser.add_argument("--interval", type=str, default="10", help="Time in seconds between frames capturd for timelapse.")
    parser.add_argument("--lat", type=float, default=DEFAULT_LAT, help="Latitude")
    parser.add_argument("--long", type=float, default=DEFAULT_LONG, help="Longitude")
    return parser.parse_args()

def main():
    args = get_args()
    
    # Setup Timezone
    try:
        tz = pytz.timezone(TIMEZONE_NAME)
    except pytz.UnknownTimeZoneError:
        print(f"Error: Unknown timezone {TIMEZONE_NAME}")
        sys.exit(1)

    # Calculate Solar Event Time
    sun = Sun(args.lat, args.long)
    now = datetime.datetime.now(tz)
    now_date = now.date()
    event_time = datetime.datetime(1970, 1, 1)
    
    while event_time.date() != now.date():
        # sometimes timezones are a bitch and I'm lazy so we're fixing this like this, there's probably a better way
        if args.mode == 'sunrise':
            event_time = sun.get_sunrise_time(now_date).astimezone(tz)
        else:
            event_time = sun.get_sunset_time(now_date).astimezone(tz)

        # now_date not used anywhere else so playing with it here
        now_date += datetime.timedelta(days=1)

#    print(f"{sun.get_sunset_time()}, or with {now.date()}->{sun.get_sunset_time(now.date())}, or with {tz}->{event_time}")
    # Calculate Recording Window
    start_time = event_time + datetime.timedelta(minutes=args.start_offset)
    end_time = event_time + datetime.timedelta(minutes=args.end_offset)
    
    # Calculate Duration and Wait Time
    duration_seconds = (end_time - start_time).total_seconds()
    wait_seconds = (start_time - now).total_seconds()

    print(f"--- SCHEDULER: {datetime.datetime.now()} ---")
    print(f"Target: {args.cam} | Event: {args.mode} at {event_time.strftime('%H:%M on %m/%d/%y')}")
    print(f"Recording Window: {start_time.strftime('%H:%M')} to {end_time.strftime('%H:%M')}")
    print(f"Duration: {int(duration_seconds)}s")

    # Safety Checks
    if duration_seconds <= 0:
        print("Error: End time is before Start time. Check offsets.")
        sys.exit(1)

    if wait_seconds < 0:
        print("Error: Start time has already passed for today.")
        print(f"{start_time.strftime('%m/%d %H:%M')} - {now.strftime('%m/%d %H:%M')} = {start_time-now} or {wait_seconds=}")
        sys.exit(1)

    # Wait for the start time
    print(f"Sleeping for {int(wait_seconds)} seconds...")
    sys.stdout.flush() # Ensure logs are written before sleep
    time.sleep(wait_seconds)

    # Trigger the Recorder
    print("Wake up! Starting recording...")
    cmd = [
        "/usr/bin/python3", RECORD_SCRIPT,
        "--cam", args.cam,
        "--duration", str(int(duration_seconds)),
        "--interval", args.interval,
        "--suffix", args.mode
    ]
    
    # Execute and capture output for the log
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"Recorder Error: {result.stderr}")

if __name__ == "__main__":
    main()
