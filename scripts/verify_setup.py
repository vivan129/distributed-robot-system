#!/usr/bin/env python3

"""

Setup Verification Script

Checks if all required files, directories, and dependencies are present

"""

import sys

import os

from pathlib import Path

from typing import List, Tuple

# ANSI color codes

GREEN = '\033[92m'

RED = '\033[91m'

YELLOW = '\033[93m'

BLUE = '\033[94m'

RESET = '\033[0m'

def print_header(text: str):

"""Print formatted header"""

print("\n" + "="*60)

print(f"{BLUE}{text}{RESET}")

print("="*60 + "\n")

def check_files() -> Tuple[List[str], List[str]]:

"""Check if required files exist"""

print("Checking required files...")

required_files = [

# Config files

'config/robot_config.yaml',

'config/slam_config.yaml',

'.env.example',

'.gitignore',

'README.md',

# PC Server

'pc_server/main.py',

'pc_server/requirements.txt',

'pc_server/modules/__init__.py',

'pc_server/modules/ai_brain.py',

'pc_server/modules/tts_engine.py',

'pc_server/modules/face_animator.py',

'pc_server/modules/slam_processor.py',

'pc_server/modules/vision_processor.py',

'pc_server/modules/voice_input.py',

'pc_server/modules/robot_controller.py',

'pc_server/templates/dashboard.html',

# Pi Client

'pi_client/main.py',

'pi_client/requirements.txt',

'pi_client/__init__.py',

'pi_client/hardware/__init__.py',

'pi_client/hardware/motor_controller.py',

'pi_client/hardware/camera_streamer.py',

'pi_client/hardware/lidar_streamer.py',

'pi_client/hardware/ultrasonic_sensor.py',

'pi_client/display/__init__.py',

'pi_client/display/face_display.py',

'pi_client/display/templates/face.html',

# Scripts

'scripts/setup_pc.sh',

'scripts/setup_pi.sh',

]

present = []

missing = []

for file in required_files:

if Path(file).exists():

present.append(file)

print(f"  {GREEN}✓{RESET} {file}")

else:

missing.append(file)

print(f"  {RED}✗{RESET} {file}")

return present, missing

def check_directories() -> Tuple[List[str], List[str]]:

"""Check if required directories exist"""

print("\nChecking required directories...")

required_dirs = [

'config',

'pc_server',

'pc_server/modules',

'pc_server/templates',

'pc_server/static',

'pi_client',

'pi_client/hardware',

'pi_client/display',

'pi_client/display/templates',

'scripts',

'logs',

'data',

]

present = []

missing = []

for directory in required_dirs:

if Path(directory).exists():

present.append(directory)

print(f"  {GREEN}✓{RESET} {directory}/")

else:

missing.append(directory)

print(f"  {RED}✗{RESET} {directory}/")

return present, missing

def check_env_file() -> bool:

"""Check if .env file exists and has required variables"""

print("\nChecking environment configuration...")

if not Path('.env').exists():

print(f"  {YELLOW}⚠{RESET} .env file not found")

print(f"    Copy .env.example to .env and configure it")

return False

print(f"  {GREEN}✓{RESET} .env file exists")

# Try to load and check

try:

from dotenv import load_dotenv

load_dotenv()

required_vars = ['GEMINI_API_KEY']

missing_vars = []

for var in required_vars:

value = os.getenv(var)

if not value or value.startswith('your_'):

missing_vars.append(var)

print(f"  {YELLOW}⚠{RESET} {var} not configured")

else:

print(f"  {GREEN}✓{RESET} {var} is set")

return len(missing_vars) == 0

except ImportError:

print(f"  {YELLOW}⚠{RESET} python-dotenv not installed, cannot verify")

return True

def check_python_dependencies() -> bool:

"""Check if Python dependencies are installed"""

print("\nChecking Python dependencies...")

pc_deps = [

'flask',

'flask_socketio',

'google.generativeai',

'edge_tts',

'speech_recognition',

'cv2',

'numpy',

'yaml',

]

pi_deps = [

'flask',

'flask_socketio',

'socketio',

'cv2',

'yaml',

]

# Determine which dependencies to check

if Path('pc_server/main.py').parent.resolve() == Path.cwd():

deps_to_check = pc_deps

print("  Checking PC server dependencies...")

elif Path('pi_client/main.py').parent.resolve() == Path.cwd():

deps_to_check = pi_deps

print("  Checking Pi client dependencies...")

else:

deps_to_check = pc_deps + pi_deps

print("  Checking all dependencies...")

missing = []

for module in deps_to_check:

try:

__import__(module)

print(f"  {GREEN}✓{RESET} {module}")

except ImportError:

missing.append(module)

print(f"  {RED}✗{RESET} {module}")

if missing:

print(f"\n  {YELLOW}Missing dependencies:{RESET} {', '.join(missing)}")

print(f"    Run: pip install -r requirements.txt")

return False

return True

def check_permissions():

"""Check file permissions"""

print("\nChecking script permissions...")

scripts = [

'scripts/setup_pc.sh',

'scripts/setup_pi.sh',

'scripts/create_directories.sh',

]

for script in scripts:

path = Path(script)

if path.exists():

if os.access(script, os.X_OK):

print(f"  {GREEN}✓{RESET} {script} is executable")

else:

print(f"  {YELLOW}⚠{RESET} {script} is not executable")

print(f"    Run: chmod +x {script}")

else:

print(f"  {RED}✗{RESET} {script} not found")

def main():

"""Main verification function"""

print_header("🔍 ROBOT SYSTEM SETUP VERIFICATION")

# Change to project root

script_dir = Path(__file__).parent

project_root = script_dir.parent

os.chdir(project_root)

print(f"Project root: {project_root}\n")

# Run checks

files_present, files_missing = check_files()

dirs_present, dirs_missing = check_directories()

env_ok = check_env_file()

deps_ok = check_python_dependencies()

check_permissions()

# Summary

print_header("📊 VERIFICATION SUMMARY")

print(f"Files: {len(files_present)}/{len(files_present) + len(files_missing)} present")

print(f"Directories: {len(dirs_present)}/{len(dirs_present) + len(dirs_missing)} present")

print(f"Environment: {GREEN + '✓ Configured' if env_ok else YELLOW + '⚠ Needs configuration'}{RESET}")

print(f"Dependencies: {GREEN + '✓ Installed' if deps_ok else RED + '✗ Missing dependencies'}{RESET}")

# Overall status

all_ok = (len(files_missing) == 0 and

len(dirs_missing) == 0 and

env_ok and

deps_ok)

print("\n" + "="*60)

if all_ok:

print(f"{GREEN}✓ SETUP VERIFICATION PASSED{RESET}")

print("="*60)

print("\nYour robot system is ready to run!")

print("\nNext steps:")

print("  1. Start PC server: cd pc_server && python main.py")

print("  2. Start Pi client: cd pi_client && python main.py")

return 0

else:

print(f"{RED}✗ SETUP VERIFICATION FAILED{RESET}")

print("="*60)

print("\nPlease fix the issues above before running the system.")

if files_missing:

print(f"\n{YELLOW}Missing files:{RESET}")

for f in files_missing[:5]:

print(f"  - {f}")

if len(files_missing) > 5:

print(f"  ... and {len(files_missing) - 5} more")

if dirs_missing:

print(f"\n{YELLOW}Missing directories:{RESET}")

print(f"  Run: ./scripts/create_directories.sh")

if not env_ok:

print(f"\n{YELLOW}Environment not configured:{RESET}")

print(f"  1. Copy .env.example to .env")

print(f"  2. Edit .env and add your GEMINI_API_KEY")

if not deps_ok:

print(f"\n{YELLOW}Dependencies not installed:{RESET}")

print(f"  Run: pip install -r requirements.txt")

return 1

if __name__ == '__main__':

sys.exit(main())