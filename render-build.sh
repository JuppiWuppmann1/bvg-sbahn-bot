#!/usr/bin/env bash
set -o errexit

echo "🚀 Installiere Python-Pakete..."
pip install -r requirements.txt

echo "📦 Installiere systemweiten Chrome..."
apt-get update && apt-get install -y chromium-browser

echo "🔧 Installiere Node-Abhängigkeiten..."
npm install

echo "🚀 Installiere Playwright-Browser..."
python -m playwright install chromium
