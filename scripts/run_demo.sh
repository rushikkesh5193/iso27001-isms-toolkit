#!/usr/bin/env bash
# Regenerate the synthetic dataset, build the example outputs and run the tests.
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m tools.gen_org examples/sample_org.json
python3 -m isms examples/sample_org.json --as-of 2026-10-24 --out-dir examples
python3 -m unittest discover -s tests
