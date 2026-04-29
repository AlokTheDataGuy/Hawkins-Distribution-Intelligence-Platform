"""
Master pipeline: regenerate all data and rebuild the database from scratch.

Usage:  python run_pipeline.py

Run this once at the start of the project, or any time you change
data generation parameters.
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent

STEPS = [
    ("1/7 Generating products",       "scripts/data_generation/generate_products.py"),
    ("2/7 Generating geography",      "scripts/data_generation/generate_geography.py"),
    ("3/7 Generating dealer network", "scripts/data_generation/generate_network.py"),
    ("4/7 Generating sales fact",     "scripts/data_generation/generate_sales.py"),
    ("5/7 Generating aux tables",     "scripts/data_generation/generate_aux_tables.py"),
    ("6/7 ETL → SQLite",              "scripts/etl/load_to_sqlite.py"),
    ("7/7 Optimize views",            "scripts/etl/optimize_views.py"),
]

ML_STEPS = [
    ("ML: Train SARIMA forecasts",    "scripts/ml/train_forecasts.py"),
    ("ML: Anomaly detection",         "scripts/ml/anomaly_detection.py"),
    ("ML: RFM segmentation",          "scripts/ml/segmentation.py"),
]


def run_steps(steps, label_prefix=""):
    for label, script in steps:
        print(f"\n▶ {label_prefix}{label}")
        result = subprocess.run(
            [sys.executable, "-u", script],
            cwd=ROOT,
            capture_output=False,
        )
        if result.returncode != 0:
            print(f"\n❌ FAILED at: {label}")
            sys.exit(1)


def run():
    import argparse
    parser = argparse.ArgumentParser(description="HDIP master pipeline")
    parser.add_argument("--skip-ml", action="store_true", help="Skip ML training (faster rebuild)")
    args = parser.parse_args()

    t0 = time.time()
    print("=" * 64)
    print("HAWKINS DISTRIBUTION INTELLIGENCE PLATFORM — Pipeline Build")
    print("=" * 64)

    run_steps(STEPS)

    if not args.skip_ml:
        print("\n" + "=" * 64)
        print("ML Training (add --skip-ml to skip this phase)")
        print("=" * 64)
        run_steps(ML_STEPS)
    else:
        print("\n[Skipped ML training — use --skip-ml to re-skip]")

    print()
    print("=" * 64)
    print(f"✅ PIPELINE COMPLETE in {time.time()-t0:.1f}s")
    print("=" * 64)
    print()
    print("Next step:")
    print("  start.bat   (launches backend + frontend together)")
    print("  — or —")
    print("  cd backend && uvicorn main:app --reload --port 8000")
    print("  cd frontend && npm run dev")
    print()


if __name__ == "__main__":
    run()
