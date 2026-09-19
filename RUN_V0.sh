#!/usr/bin/env bash

set -euo pipefail

echo "1. Build target"
python scripts/build_target.py

echo "2. Build features"
python scripts/build_features.py

echo "3. Leakage checks"
python scripts/leakage_check.py

echo "4. Train/evaluate"
python scripts/train_v0.py

echo "5. Bootstrap uncertainty"
python scripts/bootstrap_test.py

echo "6. Threshold sensitivity"
python scripts/threshold_sensitivity.py

echo "7. Figures"
python scripts/plot_results.py

echo "8. Report"
python scripts/make_report.py

echo
echo "V0 PIPELINE COMPLETE"
