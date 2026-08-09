import os
import sys

# Shortcut launcher to run root dashboard
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DASHBOARD = os.path.join(BASE_DIR, "dashboard.py")
with open(ROOT_DASHBOARD, "r", encoding="utf-8") as f:
    code = f.read()
exec(code)
