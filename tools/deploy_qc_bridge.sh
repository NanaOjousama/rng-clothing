#!/usr/bin/env bash
# Deploy the QC Bridge (dev-only; its csproj sets CopyModToGameFolder=false).
#
# Builds Release explicitly and copies THAT. `dotnet build` defaults to Debug,
# so a bare build followed by a copy from bin/Release silently ships whatever
# stale binary happened to be sitting there.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="$ROOT/test-helpers/StardewVisualQCBridge"
DEST="/run/media/deck/USD00/steamapps/common/Stardew Valley/Mods/StardewVisualQCBridge"
dotnet build "$SRC" -c Release -v q --nologo
DLL="$SRC/bin/Release/net6.0/StardewVisualQCBridge.dll"
[ -f "$DLL" ] || { echo "no Release build at $DLL" >&2; exit 1; }
cp "$DLL" "$DEST/"
echo "deployed $(stat -c%s "$DLL") bytes -> $DEST"
echo "SMAPI loads mod DLLs at startup: restart the game to pick this up."
