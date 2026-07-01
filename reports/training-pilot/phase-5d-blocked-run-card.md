# Phase 5D Real Training Backend Wiring

Status: blocked

Timestamp: 2026-07-01T00:00:00Z
Command: PYTHONPATH=src python -m visdoc_retrieve.train_lora_pilot --config configs/train_lora_pilot.local.example.json
Candidate universe: evaluated_split_pages
Max steps: 20
Sample limit: 8

Boundary: pilot, dev-only, not final benchmark.

Training did not run. This blocked run is not a real training result and does not claim benchmark gain.

Blocked reasons:
- allow_real_training_false: Config did not explicitly allow real training.
- training_env_not_enabled: VISDOC_ENABLE_REAL_TRAINING=1 is required for a real pilot.
- missing_local_model_path: local_model_path does not exist: <redacted-local-model-path>
- cuda_not_checked: CUDA was not checked because an earlier non-import gate blocked.
