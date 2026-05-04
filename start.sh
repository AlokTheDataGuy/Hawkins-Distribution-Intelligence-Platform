#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# Render boot script for HDIP backend
#
# Strategy: start uvicorn immediately so Render's health check passes,
# then build the DB in the background if it's missing.
#
# Raw CSVs are committed to git (data/raw/), so we only run the ETL step
# (DuckDB streams from disk, ~50MB peak) — not the full data generation
# pipeline (which uses 400MB+ of pandas DataFrames and causes OOM).
# ─────────────────────────────────────────────────────────────────────────────
set -uo pipefail

# Render runs this from rootDir (= backend/), so we step up to repo root
cd ..

DB_PATH="data/hawkins.db"
MIN_DB_SIZE=$((50 * 1024 * 1024))   # 50 MB sanity threshold

echo "▶ HDIP Boot Sequence"
echo "  Working dir : $(pwd)"
echo "  Python      : $(python --version 2>&1)"

# ── 1. Database check — run ETL in background if DB missing ──────────────────
if [ -f "$DB_PATH" ]; then
    db_size=$(stat -c%s "$DB_PATH" 2>/dev/null || stat -f%z "$DB_PATH" 2>/dev/null || echo 0)
else
    db_size=0
fi

if [ "$db_size" -lt "$MIN_DB_SIZE" ]; then
    echo "▶ Database missing — running ETL from committed CSVs (~1-2 min)..."
    (python scripts/etl/load_to_sqlite.py && python scripts/etl/optimize_views.py && echo "✓ Database ready") &
else
    echo "✓ Database found: $(($db_size / 1024 / 1024)) MB — skipping ETL"
fi

# ── 2. Start FastAPI immediately so health check passes ──────────────────────
echo "▶ Starting FastAPI on port ${PORT:-8000}..."
cd backend
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
