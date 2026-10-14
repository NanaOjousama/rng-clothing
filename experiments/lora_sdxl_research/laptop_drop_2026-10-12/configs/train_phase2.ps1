# Phase-2 full run (method C clean-front), then the evaluation (inference only).  Approved by user 2026-10-12.
# Try 2: no VRAM cap (try 1 ran fine; it ended by a manual restart, not a crash).  Never starts a second training run.
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTORCH_CUDA_ALLOC_CONF = 'expandable_segments:True'; $env:CLEANFRONT_VRAM_MB = '0'   # cap off (user): try 1 ran fine uncapped; the 'freeze' was a manual restart (event 1074)
$R = 'C:\Users\Chris\sdxl_lora_research'; $RUN = "$R\runs\phase2_cleanfront"; $PY = 'C:\Users\Chris\stardew-lora-lab\.venv\Scripts\python.exe'
$res = "$R\runs\phase2_cleanfront.result"
if (Test-Path $RUN) {                      # keep try 1 as evidence
  $n = 1; while (Test-Path "$RUN`_try$n") { $n++ }
  Rename-Item $RUN "phase2_cleanfront_try$n"
  foreach ($e in 'log','err','result') { if (Test-Path "$R\runs\phase2_cleanfront.$e") { Rename-Item "$R\runs\phase2_cleanfront.$e" "phase2_cleanfront_try$n.$e" } }
}
New-Item -ItemType Directory -Force $RUN | Out-Null
$p = Start-Process -PassThru -NoNewWindow -FilePath $PY -WorkingDirectory 'C:\Users\Chris\stardew-lora-lab\sd-scripts' `
  -ArgumentList "$R\tools\sdxl_train_cleanfront.py",'--config_file',"$R\configs\phase2_cleanfront_train.toml",'--clean_front_box','2,2,32,32','--clean_front_prob','0.75' `
  -RedirectStandardOutput "$R\runs\phase2_cleanfront.log" -RedirectStandardError "$R\runs\phase2_cleanfront.err"
"started pid=$($p.Id) cap=off $(Get-Date -Format s)" | Set-Content $res
$peak = 0
while (-not $p.HasExited) { $m = [int](nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits); if ($m -gt $peak) { $peak = $m; "peak_vram_MiB=$peak" | Set-Content "$R\runs\phase2_cleanfront.peak" }; Start-Sleep 5 }
"training ended peak_vram_MiB=$peak end=$(Get-Date -Format s)" | Add-Content $res
if (-not (Test-Path "$RUN\sdvhat_phase2_cleanfront.safetensors")) { "NO FINAL CHECKPOINT: evaluation not started" | Add-Content $res; exit 1 }
Start-Sleep 20
"eval started $(Get-Date -Format s)" | Add-Content $res
Start-Process -NoNewWindow -Wait -FilePath $PY -WorkingDirectory "$R\tools" -ArgumentList "$R\tools\eval_phase2.py",$RUN,"$R\runs\phase2_eval" `
  -RedirectStandardOutput "$R\runs\phase2_eval.log" -RedirectStandardError "$R\runs\phase2_eval.err"
if (Test-Path "$R\runs\phase2_eval\DONE") { "eval DONE best=$(gc "$R\runs\phase2_eval\DONE") $(Get-Date -Format s)" | Add-Content $res } else { "eval FAILED (runs\phase2_eval.err) $(Get-Date -Format s)" | Add-Content $res }
