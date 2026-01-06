#!/usr/bin/python3
import os
import json
import datetime

# --- LOAD CONFIGS ---
# --- LOAD CONFIG ---
CONFIG_PATH = os.path.join(os.path.dirname(__file__),"config.json")

try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"Critical Error: Config file not found at {CONFIG_PATH}")
    sys.exit(1)
WEBROOT = config['system']['webroot']
LOG_DIR_NAME = config['system']['log_dir']
MANIFEST_FILE = os.path.join(WEBROOT, "manifest.json")

def get_cameras():
    cameras = []
    # Scan root for directories
    try:
        for item in os.listdir(WEBROOT):
            path = os.path.join(WEBROOT, item)
            
            # Criteria: Must be a directory, not 'logs', and not contain 'noshow'
            if os.path.isdir(path) and item != LOG_DIR_NAME and "noshow" not in item and item[0] != '.':
                cameras.append(item)
    except Exception as e:
        print(f"Error scanning cameras: {e}")
    
    return sorted(cameras)

def get_logs():
    log_files = []
    log_path = os.path.join(WEBROOT, LOG_DIR_NAME)
    
    if not os.path.exists(log_path):
        return []

    try:
        # Get all files with metadata
        files = []
        for f in os.listdir(log_path):
            full_path = os.path.join(log_path, f)
            if os.path.isfile(full_path):
                # Get modification time
                mod_time = os.path.getmtime(full_path)
                files.append({
                    "name": f,
                    "timestamp": mod_time,
                    "date_str": datetime.datetime.fromtimestamp(mod_time).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sort by timestamp descending (newest first)
        files.sort(key=lambda x: x['timestamp'], reverse=True)
        log_files = files
    except Exception as e:
        print(f"Error scanning logs: {e}")

    return log_files

def main():
    data = {
        "generated_at": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "cameras": get_cameras(),
        "logs": get_logs()
    }

    with open(MANIFEST_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M%S')}  Manifest updated at {MANIFEST_FILE}")

if __name__ == "__main__":
    main()
