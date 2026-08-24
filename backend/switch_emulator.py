import sys
import os

# Redirect backend/switch_emulator.py execution to emulator/run_switches.py
EMULATOR_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "emulator"))
sys.path.insert(0, EMULATOR_DIR)

from run_switches import main

if __name__ == "__main__":
    main()
