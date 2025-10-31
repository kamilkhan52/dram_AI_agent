# DRAM Timing Optimization - Files Reference

## Project Structure

```
/home/kamil/dram-timing-optimization/
│
├── 📄 Core Implementation Files
│   ├── dramsim3_evaluator.py          # DRAMsim3 wrapper & evaluation logic (432 lines)
│   ├── timing_config.py                # Timing configuration class (78 lines)
│   ├── manual_sweep.py                 # 1D parameter sweep tool (141 lines)
│   └── test_setup.py                   # Validation test suite (169 lines)
│
├── 📊 Results & Analysis
│   ├── SUMMARY.md                      # Executive summary
│   ├── PROJECT_STATUS.md               # Complete project status & timeline
│   ├── sweep_results.json              # Manual sweep raw data
│   ├── parameter_sweep_analysis.png    # Manual sweep visualization
│   └── FILES_REFERENCE.md              # This file
│
├── 📚 Documentation
│   ├── README.md                       # Complete project documentation
│   ├── SETUP_GUIDE.md                  # Initial setup instructions
│   └── requirements.txt                # Python dependencies
│
├── 🧬 OpenEvolve/ADRS Integration
│   └── openevolve_dram/
│       ├── initial_program.py          # Baseline configuration for evolution
│       ├── evaluator.py                # Fitness function wrapper
│       ├── config.yaml                 # Evolution parameters
│       ├── system_prompt.txt           # LLM optimization instructions
│       ├── run_evolution.py            # Launch script
│       ├── README.md                   # OpenEvolve usage guide
│       ├── SETUP_COMPLETE.md           # Integration verification
│       ├── EVOLUTION_RESULTS.md        # Comprehensive results analysis
│       ├── monitor_progress.sh         # Progress monitoring script
│       └── openevolve_output/          # Evolution outputs
│           ├── best/
│           │   ├── best_program.py     # Final optimized configuration
│           │   └── best_program_info.json
│           ├── logs/
│           │   └── openevolve_20251019_221502.log  # Full evolution log
│           └── database/
│               └── map_elites.db       # Evolution history
│
└── 🔧 Test & Validation Outputs
    ├── test_outputs/                   # Test run outputs
    ├── sweep_results/                  # Manual sweep outputs
    └── openevolve_dram/eval_outputs/   # Evaluation cache
```

## Key Files by Purpose

### 🚀 Quick Start
- **SUMMARY.md** - Start here! Executive summary of results
- **README.md** - Complete usage guide
- **PROJECT_STATUS.md** - Current status and timeline

### 🔬 Running Experiments
- **manual_sweep.py** - Run parameter sweep
- **test_setup.py** - Validate setup
- **openevolve_dram/run_evolution.py** - Run evolution

### 📊 Viewing Results
- **openevolve_dram/EVOLUTION_RESULTS.md** - Detailed analysis
- **parameter_sweep_analysis.png** - Sweep visualization
- **sweep_results.json** - Raw sweep data
- **openevolve_output/best/best_program.py** - Best config

### 🛠️ Core Implementation
- **dramsim3_evaluator.py** - Main evaluation engine
- **timing_config.py** - Configuration class
- **openevolve_dram/evaluator.py** - OpenEvolve integration

### 📖 Documentation
- **README.md** - Project overview & usage
- **openevolve_dram/README.md** - OpenEvolve guide
- **SETUP_GUIDE.md** - Initial setup
- **FILES_REFERENCE.md** - This file

## File Sizes

### Code Files
- dramsim3_evaluator.py: ~15 KB
- timing_config.py: ~3 KB
- manual_sweep.py: ~5 KB
- test_setup.py: ~6 KB
- openevolve_dram/evaluator.py: ~7 KB
- openevolve_dram/initial_program.py: ~3 KB

### Documentation
- PROJECT_STATUS.md: ~8 KB
- EVOLUTION_RESULTS.md: ~12 KB
- README.md: ~10 KB
- openevolve_dram/README.md: ~11 KB
- SUMMARY.md: ~2 KB

### Data Files
- sweep_results.json: ~8 KB
- parameter_sweep_analysis.png: ~50 KB
- Evolution logs: ~500 KB

## Important Commands

### View Results
```bash
# Executive summary
cat SUMMARY.md

# Full project status
cat PROJECT_STATUS.md

# Detailed evolution results
cat openevolve_dram/EVOLUTION_RESULTS.md

# Best configuration
cat openevolve_output/best/best_program.py
```

### Run Tools
```bash
# Activate environment
conda activate dram-opt

# Run tests
python test_setup.py

# Run manual sweep
python manual_sweep.py

# Run evolution
cd openevolve_dram
export OPENAI_API_KEY='your-key'
python run_evolution.py --iterations 80
```

### Check Logs
```bash
# View evolution log
tail -100 openevolve_output/logs/openevolve_*.log

# Monitor progress (if running)
tail -f openevolve_output/logs/openevolve_*.log | grep "Iteration"
```

## Total Project Stats

- **Total Files Created:** 25+
- **Total Code Lines:** ~1,500
- **Total Documentation:** ~50 KB
- **Total Runtime:** ~20 minutes (all experiments)
- **Total Cost:** ~$1
- **Performance Improvement:** +8.86% overall, +16.81% random access

## Version Information

- **DRAMsim3:** Custom build (Oct 2025)
- **OpenEvolve:** 0.2.18
- **Python:** 3.10
- **Environment:** dram-opt (conda)

## Contact & References

- **DRAMsim3:** https://github.com/umd-memsys/DRAMsim3
- **OpenEvolve:** https://github.com/codelion/openevolve
- **ADRS Paper:** Automated Design via Repeated Sampling

---

Last Updated: October 19, 2025
