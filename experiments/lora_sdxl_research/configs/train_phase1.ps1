# Phase 1 training.  RUN ONLY AFTER USER APPROVAL (and a passing memory probe).
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTORCH_CUDA_ALLOC_CONF = 'expandable_segments:True'
$R = 'C:\Users\Chris\sdxl_lora_research'
Set-Location 'C:\Users\Chris\stardew-lora-lab\sd-scripts'      # clean upstream clone, commit 690ea7f
& 'C:\Users\Chris\stardew-lora-lab\.venv\Scripts\python.exe' sdxl_train_network.py `
  --config_file "$R\configs\phase1_front_train.toml" 2>&1 | Tee-Object "$R\runs\phase1_front.log"
