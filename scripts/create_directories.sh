#!/bin/bash

# Create Required Directories Script

# Creates all necessary directories for the robot system

set -e

echo "============================================================"

echo "📁 CREATING REQUIRED DIRECTORIES"

echo "============================================================"

echo ""

# Get script directory

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Function to create directory if it doesn't exist

create_dir() {

if [ ! -d "$1" ]; then

mkdir -p "$1"

echo "✓ Created: $1"

else

echo "  Exists: $1"

fi

}

echo "Creating PC server directories..."

create_dir "pc_server/output"

create_dir "pc_server/output/audio"

create_dir "pc_server/output/maps"

create_dir "pc_server/static"

create_dir "pc_server/static/css"

create_dir "pc_server/static/js"

create_dir "pc_server/static/images"

create_dir "pc_server/templates"

echo ""

echo "Creating Pi client directories..."

create_dir "pi_client/display/static"

create_dir "pi_client/display/static/css"

create_dir "pi_client/display/static/js"

create_dir "pi_client/display/templates"

echo ""

echo "Creating data directories..."

create_dir "data"

create_dir "data/slam"

create_dir "data/captures"

create_dir "data/recordings"

echo ""

echo "Creating log directory..."

create_dir "logs"

echo ""

echo "Creating temporary directory..."

create_dir "tmp"

echo ""

echo "Creating test directory..."

create_dir "tests"

create_dir "tests/unit"

create_dir "tests/integration"

echo ""

echo "Creating documentation directory..."

create_dir "docs"

create_dir "docs/images"

create_dir "docs/tutorials"

echo ""

echo "============================================================"

echo "✓ ALL DIRECTORIES CREATED SUCCESSFULLY"

echo "============================================================"

echo ""

echo "Directory structure:"

echo "  pc_server/output/ - TTS audio and SLAM maps"

echo "  pc_server/static/ - Dashboard assets"

echo "  pi_client/display/ - Face display assets"

echo "  data/ - Runtime data storage"

echo "  logs/ - Application logs"

echo "  tests/ - Unit and integration tests"

echo "  docs/ - Additional documentation"

echo "============================================================"