# manual_sweep.py

import json
import itertools
from dramsim3_evaluator import DRAMsim3Evaluator
import matplotlib.pyplot as plt
import numpy as np

def run_parameter_sweep():
    """
    Run a 1D parameter sweep, varying one parameter at a time
    while keeping others at baseline values.
    """
    # Initialize evaluator
    evaluator = DRAMsim3Evaluator(
        dramsim_path="/home/kamil/DRAMsim3/build/dramsim3main",
        base_config="/home/kamil/DRAMsim3/configs/DDR4_8Gb_x8_3200.ini",
        output_dir="./sweep_results"
    )
    
    # Baseline DDR4-3200 JEDEC timing parameters
    baseline = {
        'CL': 22,
        'tRCD': 22,
        'tRP': 22,
        'tRAS': 52
    }
    
    # Define parameter ranges for 1D sweep (one at a time)
    # AGGRESSIVE RANGES: Testing minimum bounds and constraint boundaries
    param_ranges = {
        'CL': [10, 12, 14, 16, 18],      # Push to minimum valid bound
        'tRCD': [10, 12, 14, 16, 18],    # Test very aggressive values
        'tRP': [10, 12, 14, 16, 18],     # Aggressive precharge timing
        'tRAS': [25, 30, 35, 40, 45]     # Test at constraint boundary (tRAS >= tRCD + CL)
    }
    
    print("=" * 70)
    print("DRAM Timing Parameter Sweep")
    print("=" * 70)
    print(f"Parameter ranges:")
    for param, values in param_ranges.items():
        print(f"  {param}: {values}")
    print(f"Total combinations: {np.prod([len(v) for v in param_ranges.values()])}")
    print("=" * 70)
    print()
    
    # Run sweep
    results = []
    
    # Sample subset for initial exploration (full sweep = 625 combinations)
    # Let's do a 1D sweep on each parameter first
    print("1D Parameter Sweeps (one parameter at a time)")
    print("-" * 70)
    
    baseline_params = {'CL': 22, 'tRCD': 22, 'tRP': 22, 'tRAS': 52}
    
    for param_name in param_ranges.keys():
        print(f"\nSweeping {param_name}:")
        
        for value in param_ranges[param_name]:
            test_params = baseline_params.copy()
            test_params[param_name] = value
            
            print(f"\n  Testing {param_name}={value}...")
            result = evaluator.evaluate_config(
                test_params,
                workloads=['random', 'stream'],
                cycles=100000
            )
            
            result['param_swept'] = param_name
            result['sweep_value'] = value
            results.append(result)
            
            if result['valid']:
                print(f"    ✓ Score: {result['score']:.4f}")
            else:
                print(f"    ✗ Invalid: {result['error_msg']}")
    
    # Save results
    with open('sweep_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "=" * 70)
    print("Sweep complete! Results saved to sweep_results.json")
    print("=" * 70)
    
    # Analysis
    analyze_sweep_results(results, param_ranges.keys())
    
    return results

def analyze_sweep_results(results, param_names):
    """Analyze and visualize sweep results."""
    
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    
    # Filter valid results
    valid_results = [r for r in results if r['valid']]
    
    print(f"\nValid configurations: {len(valid_results)}/{len(results)}")
    
    # Find best configurations
    sorted_results = sorted(valid_results, key=lambda x: x['score'], reverse=True)
    
    print("\nTop 5 configurations:")
    for i, result in enumerate(sorted_results[:5], 1):
        print(f"\n{i}. Score: {result['score']:.4f}")
        print(f"   Params: {result['timing_params']}")
        print(f"   Workload scores: {result['workload_scores']}")
    
    # Per-parameter analysis
    print("\n" + "-" * 70)
    print("Per-parameter trends:")
    print("-" * 70)
    
    for param_name in param_names:
        param_results = [r for r in valid_results if r.get('param_swept') == param_name]
        if not param_results:
            continue
            
        param_results.sort(key=lambda x: x['sweep_value'])
        
        print(f"\n{param_name}:")
        for r in param_results:
            print(f"  {r['sweep_value']:3d}: score={r['score']:.4f}")
        
        # Find optimal value
        best = max(param_results, key=lambda x: x['score'])
        print(f"  → Best value: {best['sweep_value']} (score={best['score']:.4f})")
    
    # Visualize results
    plot_sweep_results(valid_results, param_names)

def plot_sweep_results(results, param_names):
    """Create visualization of sweep results."""
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    axes = axes.flatten()
    
    for idx, param_name in enumerate(param_names):
        ax = axes[idx]
        
        param_results = [r for r in results if r.get('param_swept') == param_name]
        if not param_results:
            continue
        
        param_results.sort(key=lambda x: x['sweep_value'])
        
        values = [r['sweep_value'] for r in param_results]
        scores = [r['score'] for r in param_results]
        random_scores = [r['workload_scores'].get('random', 0) for r in param_results]
        stream_scores = [r['workload_scores'].get('stream', 0) for r in param_results]
        
        ax.plot(values, scores, 'ko-', label='Overall', linewidth=2, markersize=8)
        ax.plot(values, random_scores, 'rs--', label='Random', linewidth=1.5, markersize=6)
        ax.plot(values, stream_scores, 'b^--', label='Stream', linewidth=1.5, markersize=6)
        
        ax.axhline(y=1.0, color='gray', linestyle=':', label='Baseline')
        ax.set_xlabel(f'{param_name} (cycles)', fontsize=12)
        ax.set_ylabel('Normalized Score', fontsize=12)
        ax.set_title(f'Impact of {param_name}', fontsize=14, fontweight='bold')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('parameter_sweep_analysis.png', dpi=150, bbox_inches='tight')
    print(f"\nPlot saved to parameter_sweep_analysis.png")
    plt.show()

if __name__ == "__main__":
    results = run_parameter_sweep()
