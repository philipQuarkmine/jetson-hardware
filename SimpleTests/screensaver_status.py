#!/usr/bin/env python3
"""
screensaver_status.py

Check the status of running Jetson screensavers.
Shows process info, runtime, and provides stop functionality.

Usage:
    python3 SimpleTests/screensaver_status.py
"""

import os
import subprocess
import time


def check_screensaver_status():
    """Check if any screensavers are currently running."""
    try:
        # Check for running screensaver processes
        result = subprocess.run(
            ["pgrep", "-f", "jetson_screensaver.py|simple_screensaver.py"], 
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            print("🌙✨ JETSON SCREENSAVER STATUS")
            print("=" * 40)
            print(f"📊 Found {len(pids)} running screensaver(s)")
            print()
            
            for pid in pids:
                if pid:
                    # Get process details
                    ps_result = subprocess.run(
                        ["ps", "-p", pid, "-o", "pid,ppid,etime,cmd", "--no-headers"],
                        capture_output=True, text=True
                    )
                    
                    if ps_result.returncode == 0:
                        process_info = ps_result.stdout.strip()
                        print(f"🚀 Process: {process_info}")
            
            print()
            print("🛑 To stop all screensavers:")
            print(f"   pkill -f 'jetson_screensaver.py|simple_screensaver.py'")
            print()
            print("📋 To stop specific PID:")
            for pid in pids:
                if pid:
                    print(f"   kill {pid}")
            
        else:
            print("🌙 No screensavers currently running")
            print()
            print("🚀 To start a screensaver:")
            print("   python3 SimpleTests/screensaver_launcher.py")
    
    except Exception as e:
        print(f"❌ Error checking screensaver status: {e}")


def show_recent_log():
    """Show recent screensaver log if available."""
    log_file = "/home/phiip/workspace/jetson-hardware/screensaver_night.log"
    if os.path.exists(log_file):
        print("\n📄 Recent screensaver log:")
        print("-" * 30)
        try:
            subprocess.run(["tail", "-15", log_file])
        except Exception as e:
            print(f"❌ Could not read log: {e}")


if __name__ == "__main__":
    print("🌙 Jetson Screensaver Status Checker")
    print("Checking for running ambient display programs...")
    print()
    
    check_screensaver_status()
    show_recent_log()
