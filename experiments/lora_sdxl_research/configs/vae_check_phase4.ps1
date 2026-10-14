# VAE round-trip of the phase-4 layouts (INFERENCE ONLY, ~3 min).  Ceiling on grid exactness for 10-px (4view)
# and 20-px (front) cells; phase 3 used 12-px cells.
$R = 'C:\Users\Chris\sdxl_lora_research'; $PY = 'C:\Users\Chris\stardew-lora-lab\.venv\Scripts\python.exe'
& $PY "$R\tools\vae_roundtrip.py" "$R\dataset\phase4_4view_512\train\2_sdvhat" 10 16 "$R\runs\vae_phase4_4view.json"
& $PY "$R\tools\vae_roundtrip.py" "$R\dataset\phase4_front_512\train\2_sdvhat" 20 16 "$R\runs\vae_phase4_front.json"
& $PY "$R\tools\vae_roundtrip.py" "$R\dataset\phase3_4view_512\train\1_sdvhat" 12 16 "$R\runs\vae_phase3_ref.json"
