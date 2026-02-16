#!/usr/bin/env python3
"""Simple preferences GUI for Intervals Sync."""
import os
import sys
from pathlib import Path

try:
    import tkinter as tk
    from tkinter import messagebox, filedialog
except ImportError:
    print("tkinter not available")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
ENV_FILE = SCRIPT_DIR / ".env"


def load_env():
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            return dict(line.strip().split("=", 1) for line in f if "=" in line and not line.startswith("#"))
    return {}


def save_env(data):
    with open(ENV_FILE, "w") as f:
        for k, v in data.items():
            if v:
                f.write(f"{k}={v}\n")


class PreferencesApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Intervals Sync - Preferences")
        self.root.geometry("400x300")
        
        self.entries = {}
        
        tk.Label(self.root, text="API Configuration", font=("Arial", 14, "bold")).pack(pady=10)
        
        fields = [
            ("ATHLETE_ID", "Athlete ID"),
            ("INTERVALS_KEY", "API Key"),
            ("SYNC_DAYS", "Days to sync (default: 28)"),
        ]
        
        for key, label in fields:
            frame = tk.Frame(self.root)
            frame.pack(fill="x", padx=20, pady=5)
            tk.Label(frame, text=label, width=15, anchor="w").pack(side="left")
            entry = tk.Entry(frame)
            entry.pack(side="right", fill="x", expand=True)
            self.entries[key] = entry
        
        data = load_env()
        for key, entry in self.entries.items():
            entry.insert(0, data.get(key, ""))
        
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="Save", command=self.save, bg="#4CAF50", fg="white", width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Run Sync", command=self.run_sync, bg="#2196F3", fg="white", width=10).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Cancel", command=self.root.quit, width=10).pack(side="left", padx=5)
        
    def save(self):
        data = {k: v.get() for k, v in self.entries.items() if v.get()}
        save_env(data)
        messagebox.showinfo("Saved", "Settings saved successfully!")
        
    def run_sync(self):
        self.save()
        self.root.quit()
        os.system(f"cd '{SCRIPT_DIR}' && python3 sync.py && open latest.html")
        
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    PreferencesApp().run()
