#!/usr/bin/env bash
set -o errexit

echo "🚀 Installiere Playwright Browser..."
python -m playwright install --with-deps
