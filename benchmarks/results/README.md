# Benchmark Results

This directory stores result JSON files from benchmark runs.

## Naming conventions

- **Terminal-Bench runs:** `terminal-bench-<agent>-<date>.json`
- **Governance eval comparisons:** `comparison-<date>.json`
- **Single model eval runs:** `<model>-<date>.json`

## Viewing results

Use the scorecard renderer:

```bash
# Comparison table
python eval/scorecard.py results/comparison-YYYYMMDD-HHMMSS.json

# Single model results
python eval/scorecard.py results/model-YYYYMMDD-HHMMSS.json --single
```

## Submitting results

If you run a benchmark and want to contribute your results:

1. Include the full result JSON (not just the summary)
2. Document your hardware, model version, and any configuration changes
3. Open a PR with results in this directory
