#!/usr/bin/env python3
"""macOS app to sync Intervals.icu data and show report."""
import os
import sys
import subprocess

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    result = subprocess.run([sys.executable, "sync.py"], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    if result.returncode == 0:
        report_path = os.path.join(script_dir, "latest.md")
        if os.path.exists(report_path):
            subprocess.run(["open", report_path])
    else:
        if sys.stdin.isatty():
            input("Press Enter to exit...")

if __name__ == "__main__":
    main()
