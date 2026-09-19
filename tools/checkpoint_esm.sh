#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="archive/esm-checkpoints/ESM_${STAMP}.tar.gz"
mkdir -p "$(dirname "$OUT")"

tar -czf "$OUT"   mods/EnhancedSewingMachine   mods/EnhancedSewingMachine.Tests   docs/enhanced_sewing_machine   tools/build_esm_proof_assets.py   tools/build_variable_hat_size_lab.py   tools/compile_esm_garments.py   tools/validate_esm_garments.py   tools/validate_esm_generator_bridge.py   tools/validate_esm_tailoring_biases.py   tools/run_fitting_tests.sh   test-helpers/StardewVisualQCBridge

sha256sum "$OUT"
du -h "$OUT"
echo "ESM checkpoint: $OUT"
