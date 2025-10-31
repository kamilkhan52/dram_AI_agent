# OpenEvolve DRAM Timing Optimization

This directory contains the OpenEvolve integration for automated DRAM timing parameter optimization using the ADRS (Automated Design via Repeated Sampling) methodology.

## Overview

**What it does:** Uses LLMs with evolutionary algorithms to automatically discover optimal DDR4 timing parameters (CL, tRCD, tRP, tRAS) that maximize memory system performance.

**Why it's powerful:** Instead of manual parameter sweeps, OpenEvolve explores the optimization space intelligently, learning from previous evaluations and discovering non-obvious parameter combinations.

## Files

```
openevolve_dram/
├── initial_program.py       # Baseline DDR4-3200 JEDEC timing configuration
├── evaluator.py             # Fitness function using DRAMsim3
├── config.yaml              # OpenEvolve evolution parameters
├── system_prompt.txt        # Detailed optimization instructions for LLM
├── run_evolution.py         # Launcher script with prerequisites checking
└── README.md               # This file
```

## Quick Start

### Prerequisites

1. **Install OpenEvolve:**
   ```bash
   pip install openevolve
   ```

2. **Get a Gemini API key** (free tier available):
   - Visit: https://aistudio.google.com/apikey
   - Copy your API key

3. **Set environment variable:**
   ```bash
   export OPENAI_API_KEY="your-gemini-api-key-here"
   ```

### Running Evolution

**Start evolution (80 iterations):**
```bash
cd /home/kamil/dram-timing-optimization/openevolve_dram
python run_evolution.py
```

**Custom iteration count:**
```bash
python run_evolution.py --iterations 200
```

**Resume from checkpoint:**
```bash
python run_evolution.py --resume
```

### Expected Resources

- **Cost:** $1-4 for 80 iterations (using Gemini 2.0 Flash)
- **Time:** 1-2 hours for 80 iterations
- **Evaluations:** ~160 DRAMsim3 simulations (2 workloads × 80 iterations)

## How It Works

### 1. MAP-Elites Quality-Diversity Algorithm

OpenEvolve uses MAP-Elites to maintain a diverse population of solutions organized across multiple feature dimensions:

- **Latency improvement** (10 bins): 0.90x to 1.10x
- **Bandwidth improvement** (10 bins): 0.95x to 1.05x
- **Energy efficiency** (10 bins): 0.95x to 1.05x

This creates a 10×10×10 = 1000-cell grid where each cell contains the best solution for that specific combination of characteristics.

### 2. Island-Based Evolution

Three independent populations ("islands") evolve in parallel:
- Prevents premature convergence to local optima
- Exchange best solutions every 10 generations
- Maintains genetic diversity

### 3. Inspiration-Based Mutation

Each generation, the LLM receives:
- **3 top-performing programs** (best scores)
- **2 diverse programs** (different feature space regions)
- **Execution artifacts** (performance metrics, constraint violations)
- **System prompt** (domain knowledge and optimization strategies)

The LLM then generates a new configuration inspired by successful patterns.

### 4. Constraint-Aware Evaluation

Every configuration is validated before simulation:
```python
# Physical constraint
tRAS >= tRCD + CL

# Parameter bounds
10 ≤ CL ≤ 30
10 ≤ tRCD ≤ 30
10 ≤ tRP ≤ 30
25 ≤ tRAS ≤ 80
```

Invalid configurations receive score=0.0 with detailed error messages in artifacts.

## Configuration Details

### Evolution Parameters (`config.yaml`)

```yaml
max_iterations: 80           # Total evolution generations
random_seed: 42              # For reproducibility

llm:
  models:
    - gemini-2.0-flash-exp   # Fast, creative (70% weight)
    - gemini-2.0-flash-thinking-exp  # Deep reasoning (30% weight)
  temperature: 0.8           # Higher = more exploration

database:
  population_size: 50        # Programs per island
  num_islands: 3             # Parallel populations
  migration_interval: 10     # Exchange solutions every N generations
  
prompt:
  num_top_programs: 3        # Best performers for inspiration
  num_diverse_programs: 2    # Diverse solutions for exploration
```

### System Prompt Strategy

The `system_prompt.txt` file provides the LLM with:

1. **Domain knowledge:** DRAM timing parameter descriptions
2. **Physical constraints:** tRAS >= tRCD + CL requirement
3. **Proven strategies:** From manual sweep results (CL=18, tRP=10-14)
4. **Performance pitfalls:** CL<16 causes degradation
5. **Evolution tactics:** Phase-based optimization approach

This prompt was crafted based on insights from manual parameter sweeps.

## Monitoring Progress

### Real-Time Logs

OpenEvolve prints progress to stdout:
```
Generation 10/80: best_score=1.0261 (random=1.0405, stream=1.0119)
  Top config: CL=18, tRCD=22, tRP=22, tRAS=52
  
Generation 20/80: best_score=1.0312 (random=1.0489, stream=1.0138)
  Top config: CL=18, tRCD=12, tRP=10, tRAS=30
```

### Checkpoints

Saved every 10 iterations in `openevolve_output/checkpoints/`:
```
checkpoint_10/
  ├── database.pkl          # MAP-Elites archive
  ├── best_program.py       # Best configuration so far
  └── metrics.json          # Performance metrics
```

### Visualization

After evolution completes:
```bash
# Install visualization dependencies
pip install -r ../scripts/requirements.txt

# Launch interactive visualizer
python -m openevolve.scripts.visualizer
```

This shows:
- Evolution tree (parent-child relationships)
- Performance over time
- MAP-Elites grid occupancy
- Code diffs between generations

## Understanding Results

### Output Structure

```
openevolve_output/
├── best_program.py          # Best timing configuration found
├── evolution_metrics.json   # Detailed performance data
├── archive/                 # All evaluated programs
├── checkpoints/             # Periodic saves
└── logs/                    # Execution logs
```

### Best Program Format

The best configuration is saved as a complete Python program:

```python
class TimingConfiguration:
    def __init__(self):
        self.CL = 18      # Evolved value
        self.tRCD = 12    # Evolved value
        self.tRP = 10     # Evolved value
        self.tRAS = 30    # Evolved value
    # ... rest of implementation
```

### Metrics Analysis

Check `evolution_metrics.json` for:
```json
{
  "best_overall_score": 1.0312,
  "best_random_score": 1.0489,
  "best_stream_score": 1.0138,
  "best_params": {"CL": 18, "tRCD": 12, "tRP": 10, "tRAS": 30},
  "generations_to_best": 20,
  "total_evaluations": 160
}
```

## Testing Best Configuration

### Extract and Validate

```bash
# Import and test the best configuration
python << 'EOF'
import sys
sys.path.insert(0, 'openevolve_output')
from best_program import evaluate_timing_configuration

config = evaluate_timing_configuration()
print("Best parameters found:")
print(config.get_params())

is_valid, msg = config.validate()
print(f"\nValidation: {msg}")
EOF
```

### Full Evaluation

```bash
# Run full evaluation with the best config
cd /home/kamil/dram-timing-optimization
python << 'EOF'
import sys
sys.path.insert(0, 'openevolve_dram/openevolve_output')
from best_program import evaluate_timing_configuration
from dramsim3_evaluator import DRAMsim3Evaluator

config = evaluate_timing_configuration()
evaluator = DRAMsim3Evaluator(
    dramsim_path="/home/kamil/DRAMsim3/build/dramsim3main",
    base_config="/home/kamil/DRAMsim3/configs/DDR4_8Gb_x8_3200.ini",
    output_dir="./final_test_outputs"
)

result = evaluator.evaluate_config(config)
print(f"Overall Score: {result['overall_score']:.4f}")
print(f"Random Score: {result['workloads']['random']['score']:.4f}")
print(f"Stream Score: {result['workloads']['stream']['score']:.4f}")
EOF
```

## Troubleshooting

### Common Issues

**1. "ModuleNotFoundError: No module named 'openevolve'"**
```bash
pip install openevolve
```

**2. "OPENAI_API_KEY not set"**
```bash
export OPENAI_API_KEY="your-gemini-api-key"
```

**3. Evolution stuck at score ~1.0000**

This means the LLM is generating configurations similar to baseline. Try:
- Increase temperature in `config.yaml` (e.g., 0.9)
- Add more diverse programs: `num_diverse_programs: 3`
- Check system_prompt.txt includes manual sweep insights

**4. Many constraint violations**

The LLM is generating invalid configurations. Strengthen the constraint guidance in `system_prompt.txt`:
```
⚠️ CRITICAL: tRAS MUST BE >= tRCD + CL
Example: If CL=18 and tRCD=12, then tRAS ≥ 30
```

**5. API rate limiting**

Gemini free tier has rate limits. Solutions:
- Add delays in config: `api_delay: 1.0` (1 second between calls)
- Reduce parallel evaluations
- Use fewer islands: `num_islands: 1`

### Debug Mode

Enable verbose logging:
```yaml
# config.yaml
output:
  log_level: "DEBUG"
```

This shows detailed LLM prompts and responses.

## Advanced Usage

### Custom Feature Dimensions

Add your own quality-diversity dimensions:

```python
# evaluator.py
return EvaluationResult(
    metrics={
        "combined_score": overall_score,
        "row_hit_rate": result['row_hit_rate'],  # Custom metric
        "power_efficiency": custom_power_metric,  # Custom metric
        # ...
    }
)
```

```yaml
# config.yaml
database:
  feature_dimensions:
    - "latency_improvement"
    - "row_hit_rate"        # Your custom dimension
    - "power_efficiency"    # Your custom dimension
```

### Temperature Scheduling

Vary exploration over time:

```yaml
llm:
  temperature_schedule:
    0: 0.9      # High exploration early
    40: 0.7     # Moderate mid-evolution
    70: 0.5     # Exploitation near end
```

### Multi-Model Ensemble

Use different models for different stages:

```yaml
llm:
  models:
    - name: "gemini-2.0-flash-exp"
      weight: 0.5
    - name: "gpt-4o"
      weight: 0.3
    - name: "claude-3-5-sonnet"
      weight: 0.2
```

## Expected Outcomes

Based on manual sweep results, OpenEvolve should discover:

**Conservative optimizations (likely):**
- CL=18, score ~1.026 (+2.6%)
- tRP=10-14, score ~1.02 (+2%)

**Aggressive optimizations (possible):**
- CL=18 + tRP=10 combination: score ~1.035-1.045 (+3.5-4.5%)
- Multi-parameter tuning: score >1.05 (+5% improvement)

**State-of-the-art (goal):**
- Novel parameter combinations not explored in manual sweep
- Potential score >1.10 (+10% improvement)

## References

- **OpenEvolve:** https://github.com/codelion/openevolve
- **DRAMsim3:** https://github.com/umd-memsys/DRAMsim3
- **ADRS Paper:** Automated Design via Repeated Sampling
- **MAP-Elites:** Quality-Diversity optimization algorithm

## Support

For issues specific to:
- **OpenEvolve framework:** https://github.com/codelion/openevolve/issues
- **DRAM optimization:** Check ../PROJECT_STATUS.md and ../README.md
- **DRAMsim3:** https://github.com/umd-memsys/DRAMsim3/issues
