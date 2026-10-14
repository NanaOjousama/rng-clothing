# Phase 4: four-view LoRA, then its eval, then the front LoRA, then its eval.  PREPARED 2026-10-14 - NOT RUN.
# Needs explicit user approval.  Never starts two trainings at once (each step waits for the previous one).
# Order: 4view first (main question: does it rotate all four witch families?), so it can be judged while
# the front LoRA trains.  Estimates (measured 512 speed 1.06-1.89 s/it): 4view 5640 steps ~1.7-3.0 h,
# eval ~1.2 h; front 5760 steps ~1.7-3.0 h (phase 1 ran 3.05 s/it -> up to 4.9 h), eval ~1 h, variety test ~45-50 min.
param([switch]$FourViewOnly, [switch]$FrontOnly)
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTORCH_CUDA_ALLOC_CONF = 'expandable_segments:True'; $env:CLEANFRONT_VRAM_MB = '0'
$R = 'C:\Users\Chris\sdxl_lora_research'; $PY = 'C:\Users\Chris\stardew-lora-lab\.venv\Scripts\python.exe'; $SD = 'C:\Users\Chris\stardew-lora-lab\sd-scripts'
$res = "$R\runs\phase4.result"
function Train($name, $script, $extra) {
  $RUN = "$R\runs\$name"
  if (Test-Path "$RUN\*.safetensors") { "$name exists, refusing to overwrite" | Add-Content $res; return $false }
  New-Item -ItemType Directory -Force $RUN | Out-Null
  $args_ = @($script, '--config_file', "$R\configs\$name`_train.toml") + $extra
  $p = Start-Process -PassThru -NoNewWindow -FilePath $PY -WorkingDirectory $SD -ArgumentList $args_ `
       -RedirectStandardOutput "$R\runs\$name.log" -RedirectStandardError "$R\runs\$name.err"
  "$name started pid=$($p.Id) $(Get-Date -Format s)" | Add-Content $res; $peak = 0
  while (-not $p.HasExited) { $m = [int](nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits); if ($m -gt $peak) { $peak = $m; "peak_vram_MiB=$peak" | Set-Content "$R\runs\$name.peak" }; Start-Sleep 5 }
  "$name ended peak_vram_MiB=$peak $(Get-Date -Format s)" | Add-Content $res
  return (Test-Path "$RUN\sdvhat_$name.safetensors")
}
function Eval($script, $argv, $out) {
  "eval $out started $(Get-Date -Format s)" | Add-Content $res
  Start-Process -NoNewWindow -Wait -FilePath $PY -WorkingDirectory "$R\tools" -ArgumentList (@("$R\tools\$script") + $argv) `
    -RedirectStandardOutput "$R\runs\$out.log" -RedirectStandardError "$R\runs\$out.err"
  $done = "$R\runs\$out\DONE"
  if (Test-Path $done) {
    $best = (Get-Content $done -Raw).Trim()
    "eval $out DONE best=$best $(Get-Date -Format s)" | Add-Content $res
    # This is an ON-COMPLETION upload. No polling or uploads during training.
    # Only final comparison sheets and a short note go to TFWR's separate lora-reviews branch.
    try {
      $finalizer = "$R\tools\complete_lora_review.ps1"
      if (-not (Test-Path $finalizer)) { throw "Review finalizer missing: $finalizer" }
      $sheetDir = if ($out -eq 'phase4_eval') { "$R\runs\$out\sheets" } else { "$R\runs\$out" }
      $pattern = if ($out -eq 'phase4_eval') { '*_x*.png' } elseif ($out -eq 'phase4_variety') { 'variety_*_x*.png' } else { 'front_compare_x*.png' }
      $seedNote = if ($out -eq 'phase4_variety') { '101-108' } else { '7,8,9' }
      $reviewFiles = @(Get-ChildItem -LiteralPath $sheetDir -File -Filter $pattern | Select-Object -ExpandProperty FullName)
      if ($reviewFiles.Count -eq 0) { throw "No finished review sheets found in $sheetDir" }
      $note = "$R\runs\$out\REVIEW_SUMMARY.md"
      @("# $out", "", "Status: evaluation complete", "Best checkpoint: $best", "Seeds: $seedNote", "Review sheets: $($reviewFiles.Count)", "This is experimental model output, not approved mod content.") |
        Set-Content -LiteralPath $note -Encoding UTF8
      $reviewFiles += $note
      & $finalizer -Experiment $out -Files $reviewFiles -Checkpoint $best -Seeds $seedNote
      if ($LASTEXITCODE -ne 0) { throw "Review finalizer exited with $LASTEXITCODE" }
      "eval $out auto-published to GitHub lora-reviews $(Get-Date -Format s)" | Add-Content $res
    } catch {
      "eval $out auto-publish failed (results still local): $($_.Exception.Message)" | Add-Content $res
    }
  } else {
    "eval $out FAILED $(Get-Date -Format s)" | Add-Content $res
  }
}
if (-not $FrontOnly) {
  if (Train 'phase4_4view' "$R\tools\sdxl_train_cleanfront.py" @('--clean_front_box', '2,2,32,32', '--clean_front_prob', '0.75')) {
    Start-Sleep 20; Eval 'eval_phase4.py' @("$R\runs\phase4_4view", "$R\runs\phase3_cleanfront_resume\sdvhat_phase3_cleanfront.safetensors", "$R\runs\phase4_eval") 'phase4_eval'
  } else { "phase4_4view: NO FINAL CHECKPOINT" | Add-Content $res }
}
if (-not $FourViewOnly) {
  if (Train 'phase4_front' "$SD\sdxl_train_network.py" @()) {
    Start-Sleep 20; Eval 'eval_front_phase4.py' @("$R\runs\phase4_front", "$R\runs\phase1_front_512\sdvhat_phase1_front_512.safetensors", "$R\runs\phase4_front_eval") 'phase4_front_eval'
    # variety test (copies vs new silhouettes per witch family; ~256 renders, ~45-50 min).  Needs the front eval's summary.json.
    if (Test-Path "$R\runs\phase4_front_eval\DONE") {
      Eval 'eval_variety_phase4.py' @("$R\runs\phase4_front", "$R\runs\phase1_front_512\sdvhat_phase1_front_512.safetensors", "$R\runs\phase4_front_eval", "$R\runs\phase4_variety") 'phase4_variety'
    }
  } else { "phase4_front: NO FINAL CHECKPOINT" | Add-Content $res }
}
