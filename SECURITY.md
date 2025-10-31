# Security and Setup Notes

## ⚠️ IMPORTANT: Before Using This Repository

### API Keys and Secrets

This project uses **Google Gemini API** for LLM-based optimization. The API key is **NOT included** in this repository.

**To use the evolution features:**

1. Get your own Gemini API key from: https://aistudio.google.com/apikey
2. Set it as an environment variable:
   ```bash
   export OPENAI_API_KEY="your-gemini-api-key-here"
   ```
3. **NEVER commit your API key** to version control

### Local Paths

This repository contains **hardcoded paths** that are specific to the development environment:

- DRAMsim3 path: `/home/kamil/DRAMsim3`
- Project path: `/home/kamil/dram-timing-optimization`

**You will need to modify these paths** in the following files:
- `dramsim3_evaluator.py`
- `manual_sweep.py`
- `openevolve_dram/evaluator.py`
- `openevolve_dram/run_evolution.py`
- `test_setup.py`

### Prerequisites

1. **DRAMsim3**: You must install DRAMsim3 separately
   - Repository: https://github.com/umd-memsys/DRAMsim3
   - Build instructions in their README
   - Update paths in the code to match your installation

2. **Python Environment**:
   ```bash
   conda create -n dram-opt python=3.10
   conda activate dram-opt
   pip install -r requirements.txt
   ```

3. **OpenEvolve** (for autonomous optimization):
   ```bash
   pip install openevolve
   ```

## What's Excluded from Git

The `.gitignore` file excludes:
- All output directories (`eval_outputs/`, `test_outputs/`, `openevolve_output/`)
- Python cache files (`__pycache__/`)
- Large result files and visualizations
- Log files
- API keys and secrets

These directories will be **recreated automatically** when you run the tools.

## Sensitive Information Check

Before pushing any changes:
1. ✅ No API keys in code
2. ✅ No passwords or secrets
3. ✅ No personal data
4. ✅ Large output files excluded
5. ⚠️ Local paths present (document in README)

## License

This project uses DRAMsim3, which is licensed under the MIT License.
