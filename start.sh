#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Render boot script for HDIP backend
#
# Responsibilities:
#   1. Ensure the SQLite database exists (regenerate if missing — first boot)
#   2. Start FastAPI via uvicorn on the port Render assigns
#
# The DB is NOT committed to git (it's 192 MB), so on a fresh deploy we
# regenerate it from synthetic data scripts. Subsequent deploys keep the
# DB on Render's persistent disk if attached, OR regenerate it (~2-3 min).
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

# Render runs this from rootDir (= backend/), so we step up to repo root
cd ..

DB_PATH="data/hawkins.db"
MIN_DB_SIZE=$((50 * 1024 * 1024))   # 50 MB sanity threshold

echo "▶ HDIP Boot Sequence"
echo "  Working dir : $(pwd)"
echo "  Python      : $(python --version 2>&1)"

# ── 1. Database check ────────────────────────────────────────────────────────
if [ -f "$DB_PATH" ]; then
    db_size=$(stat -c%s "$DB_PATH" 2>/dev/null || stat -f%z "$DB_PATH" 2>/dev/null || echo 0)
else
    db_size=0
fi

if [ "$db_size" -lt "$MIN_DB_SIZE" ]; then
    echo "▶ Database missing or undersized ($(($db_size / 1024 / 1024)) MB)"
    echo "▶ Running full pipeline — this takes ~2-3 minutes on first boot..."
    python run_pipeline.py
    echo "✓ Pipeline complete"
else
    echo "✓ Database found: $(($db_size / 1024 / 1024)) MB — skipping regeneration"
fi

# ── 2. Start FastAPI ─────────────────────────────────────────────────────────
echo "▶ Starting FastAPI on port ${PORT:-8000}..."
cd backend
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
