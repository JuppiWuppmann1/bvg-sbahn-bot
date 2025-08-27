#!/usr/bin/env bash
set -o errexit

echo "🚀 Installiere Python-Pakete..."
pip install -r requirements.txt

echo "🚀 Installiere Playwright Browser..."
python -m playwright install chromium
