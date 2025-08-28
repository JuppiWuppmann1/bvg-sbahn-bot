#!/usr/bin/env bash
set -o errexit

echo "🚀 Installiere Python-Pakete..."
pip install -r requirements.txt

echo "📦 Installiere systemweiten Chromium..."
apt-get update && apt-get install -y chromium

echo "🔧 Installiere Node-Abhängigkeiten..."
npm install
