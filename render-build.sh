#!/usr/bin/env bash
# Exit bei Fehlern
set -o errexit

# Installiere Dependencies
pip install -r requirements.txt

# Installiere Playwright Browser
python -m playwright install --with-deps chromium
