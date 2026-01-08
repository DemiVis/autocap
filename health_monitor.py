#!/usr/bin/python3
import sys
import argparse
import logging
from datetime import datetime
import subprocess

# Configure a basic format for logs
LOG_FORMAT = '%(asctime)s | %(message)s'

def get_cpu_temperature_f():
    """
    Reads the system temperature from the thermal zone file.
    Returns the temperature in Fahrenheit as a float.
    Returns None if the file cannot be read.
    """
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_c_millidegrees = int(f.readline().strip())
            temp_c = temp_c_millidegrees / 1000.0
            temp_f = (temp_c * 9.0 / 5.0) + 32.0
            return round(temp_f, 2)
    except FileNotFoundError:
        logging.error("Could not find thermal zone file. Is this running on a Raspberry Pi?")
        return None
    except Exception as e:
        logging.error(f"Error reading temperature: {e}")
        return None

def get_wifi_signal_strength():
    """
    Reads /proc/net/wireless to find the signal strength (dBm) and link quality.
    Returns a dictionary {'signal_level': int, 'link_quality': int/float} or None.
    Note: Signal level is usually negative (dBm).
    """
    try:
        with open("/proc/net/wireless", "r") as f:
            lines = f.readlines()
            for line in lines:
                if "wlan0" in line:
                    # Typical line format:
                    # wlan0: 0000   56.  -54.  -256        0      0      0      0      0        0
                    parts = line.split()
                    
                    # The parts list index depends on the split, but usually:
                    # parts[0] is 'wlan0:'
                    # parts[2] is Link Quality (e.g., 56.)
                    # parts[3] is Signal Level (e.g., -54.)
                    
                    # Clean the trailing dots if present
                    quality = float(parts[2].replace('.', ''))
                    signal = float(parts[3].replace('.', ''))
                    
                    return {
                        "link_quality": quality,
                        "signal_level_dbm": signal
                    }
        # If wlan0 was not found in the loop
        return None
            
    except FileNotFoundError:
        logging.error("/proc/net/wireless not found.")
        return None
    except Exception as e:
        logging.error(f"Error reading wifi signal: {e}")
        return None

def get_system_status():
    """
    Wrapper function to get all stats at once.
    Useful when importing this script as a module.
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "cpu_temp_f": get_cpu_temperature_f(),
        "wifi_status": get_wifi_signal_strength()
    }

def setup_logging(log_file=None):
    """
    Sets up the logging configuration.
    If log_file is provided, writes to file. Otherwise, prints to console.
    """
    if log_file:
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format=LOG_FORMAT
        )
    else:
        logging.basicConfig(
            stream=sys.stdout,
            level=logging.INFO,
            format=LOG_FORMAT
        )

def main():
    parser = argparse.ArgumentParser(description="Raspberry Pi Temperature and Wi-Fi Monitor")
    parser.add_argument(
        '-o', '--output', 
        type=str, 
        help="Path to the log file (e.g., /home/pi/logs/rpi_monitor.log). If omitted, prints to console."
    )
    
    args = parser.parse_args()
    
    setup_logging(args.output)
    
    temp = get_cpu_temperature_f()
    wifi = get_wifi_signal_strength()
    
    log_message = []
    
    if temp is not None:
        log_message.append(f"Temp: {temp}°F")
    else:
        log_message.append("Temp: N/A")
        
    if wifi:
        log_message.append(f"Wi-Fi Signal: {wifi['signal_level_dbm']} dBm (Quality: {wifi['link_quality']})")
    else:
        log_message.append("Wi-Fi: Not connected or Interface not found")
        
    logging.info(" | ".join(log_message))

if __name__ == "__main__":
    main()