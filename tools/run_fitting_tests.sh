#!/usr/bin/env bash
# Headless checks over the fitting mod's pure logic.
#
# Runs against the REAL generated sidecars in test-packs/, so a generator
# change that breaks the mod's assumptions fails here rather than in game.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dotnet run --project "$ROOT/mods/RNGClothingFitting.Tests" -v q --nologo
