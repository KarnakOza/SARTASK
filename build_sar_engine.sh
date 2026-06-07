#!/bin/bash
# Compiles all C source files into sar_engine.so for Linux/Streamlit Cloud
# This script is called automatically at deploy time via .streamlit/config or packages.txt

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Building sar_engine.so..."

gcc -shared -fPIC -o sar_engine.so \
    orbit.c orbital_position.c eci_position.c eci_to_ecef.c \
    doppler.c geometry.c sar_range.c vec3.c telemetry.c \
    -lm

echo "Build complete: sar_engine.so"
