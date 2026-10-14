# Memory probe: 20 steps, nothing saved for use.  RUN ONLY AFTER USER APPROVAL.
$env:PYTHONIOENCODING = 'utf-8'; $env:PYTORCH_CUDA_ALLOC_CONF = 'expandable_segments:True'
$R = 'C:\Users\Chris\sdxl_lora_research'
Set-Location 'C:\Users\Chris\stardew-lora-lab\sd-scripts'      # clean upstream clone, commit 690ea7f
& 'C:\Users\Chris\stardew-lora-lab\.venv\Scripts\python.exe' sdxl_train_network.py `
  --config_file "$R\configs\phase1_front_train.toml" `
  --max_train_steps 20 --max_train_epochs 1 --output_dir "$R\runs\memory_probe" --sample_every_n_epochs 999 `
  2>&1 | Tee-Object "$R\runs\memory_probe.log"
nvidia-smi --query-gpu=memory.used,memory.total --format=csv
