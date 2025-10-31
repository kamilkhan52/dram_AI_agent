# DRAM Timing Parameter Optimization Project

This project implements an optimization framework for DDR4 DRAM timing parameters using DRAMsim3 simulator and ADRS (Automated Design via Repeated Sampling) methodology.

## Project Structure

```
dram-timing-optimization/
├── dramsim3_evaluator.py      # Main evaluator class wrapping DRAMsim3
├── timing_config.py            # Solution representation (DRAM timing configuration)
├── manual_sweep.py             # Parameter space exploration tool
├── test_setup.py               # Validation tests
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── eval_outputs/               # Simulation results (created automatically)
├── sweep_results/              # Manual sweep outputs (created automatically)
└── test_outputs/               # Test run outputs (created automatically)
```

## Installation

### Prerequisites
- DRAMsim3 installed at `/home/kamil/DRAMsim3`
- Python 3.7+ (conda environment recommended)

### Setup Steps

1. **Create conda environment:**
```bash
conda create -n dram-opt python=3.10
conda activate dram-opt
```

2. **Install dependencies:**
```bash
cd /home/kamil/dram-timing-optimization
pip install -r requirements.txt
```

3. **Verify DRAMsim3 works:**
```bash
cd /home/kamil/DRAMsim3
./build/dramsim3main configs/DDR4_8Gb_x8_3200.ini --stream random -c 10000
```

## Usage

### Phase 0: Validation (Required First Step)

Run the test suite to validate everything is working:

```bash
cd /home/kamil/dram-timing-optimization
python test_setup.py
```

**Expected output:** All 4 tests should pass:
- ✓ PASS: Evaluator Initialization
- ✓ PASS: Configuration Class
- ✓ PASS: End-to-End Pipeline
- ✓ PASS: Constraint Boundaries

### Phase 1: Manual Parameter Sweep (Recommended)

Explore the parameter space to understand performance characteristics:

```bash
python manual_sweep.py
```

This will:
- Test 20 configurations (5 values × 4 parameters)
- Take ~5-10 minutes with fast DRAMsim3 (0.13s per 100K cycle simulation)
- Generate `sweep_results.json` with detailed metrics
- Create `parameter_sweep_analysis.png` visualization

**What to look for:**
- Which parameters have the biggest performance impact
- Typical score improvements achievable (baseline = 1.0)
- Any surprising parameter interactions

### Phase 2: ADRS Optimization (Coming Soon)

The next phase will integrate with OpenEvolve for automated optimization.

## DRAM Timing Parameters

The optimization targets 4 critical timing parameters:

### CL (CAS Latency)
- **Range:** 10-30 cycles
- **Baseline (DDR4-3200):** 22 cycles
- **Impact:** Read latency
- **Trade-off:** Lower = faster reads, but needs signal integrity margin

### tRCD (RAS to CAS Delay)
- **Range:** 10-30 cycles  
- **Baseline:** 22 cycles
- **Impact:** Row access speed
- **Trade-off:** Lower = faster row opening, but risks sense amp errors

### tRP (Row Precharge Time)
- **Range:** 10-30 cycles
- **Baseline:** 22 cycles
- **Impact:** Row switching speed
- **Trade-off:** Lower = faster row closes, but may corrupt data

### tRAS (Row Active Strobe)
- **Range:** 25-80 cycles
- **Baseline:** 52 cycles
- **Impact:** Minimum row open time
- **Trade-off:** Lower = more scheduling flexibility, but risks data loss

### Constraints

**Critical constraint:** `tRAS >= tRCD + CL`

This ensures rows stay open long enough for both activation and data access.

## Performance Metrics

Configurations are scored on three weighted components:

1. **Read Latency (40% weight):** Lower is better
   - Baseline: ~775 cycles (random workload)
   
2. **Memory Bandwidth (40% weight):** Higher is better
   - Baseline: ~18.8 MB/s (random workload)
   
3. **Energy Efficiency (20% weight):** Lower energy/access is better
   - Baseline: ~17,000 pJ per access

**Overall Score** = Geometric mean of workload scores
- Score = 1.0 → Matches baseline
- Score = 1.1 → 10% improvement
- Score = 1.2 → 20% improvement

## Workload Types

### Random Workload
- Completely random memory addresses
- Low row buffer hit rate (~0.1%)
- Benefits from fast row switching (low tRP, tRCD)

### Stream Workload  
- Sequential memory addresses
- High row buffer hit rate (can be >80%)
- Benefits from low CL and optimal tRAS

## Example Results

From manual testing with more aggressive timings:
```python
# Modified configuration
params = {'CL': 20, 'tRCD': 20, 'tRP': 20, 'tRAS': 45}

# Results
Score: 1.05-1.15 (5-15% improvement expected)
Random workload: Improved latency, similar bandwidth
Stream workload: Better overall due to lower CL
```

## File Descriptions

### dramsim3_evaluator.py
Core evaluator that:
- Parses and modifies DRAMsim3 .ini config files
- Runs simulations with different timing parameters
- Extracts metrics from JSON output
- Computes normalized performance scores
- Validates timing constraints

Key method: `evaluate_config(timing_params, workloads, cycles)`

### timing_config.py
Defines `TimingConfiguration` class:
- Stores the 4 timing parameters
- Provides `get_params()` for evaluation
- Includes `validate()` for constraint checking
- This class will be evolved by ADRS/LLM

### manual_sweep.py
Parameter space exploration tool:
- 1D sweep (one parameter at a time)
- Generates performance plots
- Identifies trends and optimal ranges
- Saves results to JSON for analysis

### test_setup.py
Comprehensive test suite:
1. Evaluator initialization
2. Configuration validation
3. End-to-end simulation pipeline
4. Constraint boundary testing

## Troubleshooting

### Test failures

**"Baseline test failed":**
- Check DRAMsim3 is built and accessible
- Verify config file exists: `/home/kamil/DRAMsim3/configs/DDR4_8Gb_x8_3200.ini`

**"Simulation timeout":**
- DRAMsim3 may have crashed - check simulation output
- Increase timeout in `_run_simulation()` if needed

### Performance issues

**Simulations too slow:**
- DRAMsim3 should run 100K cycles in ~0.13s
- Check system load and available CPU
- Consider reducing cycles for initial testing

## Next Steps

1. ✅ **Setup validation** - Run `test_setup.py`
2. ✅ **Manual sweep** - Run `manual_sweep.py` to understand the space
3. ⏳ **OpenEvolve integration** - Configure ADRS optimization (coming next)
4. ⏳ **Run evolution** - 80 iterations, ~$15-20 cost, 1-2 hours
5. ⏳ **Analyze results** - Extract best configuration and insights

## References

- DRAMsim3: https://github.com/umd-memsys/DRAMsim3
- OpenEvolve: https://github.com/codelion/openevolve
- ADRS Paper: "Automated Design via Repeated Sampling"
- DDR4 JEDEC Standard: Timing specifications

## License

This project uses DRAMsim3 which is licensed under the MIT License.
