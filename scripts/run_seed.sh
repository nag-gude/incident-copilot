#!/bin/bash
# Seed demo data - run from IncidentCopilot root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$(dirname "$SCRIPT_DIR")"
python scripts/seed_demo_data.py "$@"
