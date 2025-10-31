#!/usr/bin/env python3
"""
Run OpenEvolve DRAM Timing Optimization

This script launches the OpenEvolve evolution process for DRAM timing optimization.
It uses the ADRS (Automated Design via Repeated Sampling) methodology to discover
optimal timing parameters.

Usage:
    python run_evolution.py [--iterations N] [--resume]
    
Examples:
    # Start fresh evolution for 80 iterations
    python run_evolution.py
    
    # Run with custom iteration count
    python run_evolution.py --iterations 200
    
    # Resume from checkpoint
    python run_evolution.py --resume
"""

import os
import sys
import argparse
from pathlib import Path
import subprocess


def check_prerequisites():
    """Check that all required components are present."""
    print("🔍 Checking prerequisites...")
    
    # Check if OpenEvolve is installed
    try:
        import openevolve
        print(f"  ✓ OpenEvolve installed (version: {openevolve.__version__})")
    except ImportError:
        print("  ✗ OpenEvolve not installed!")
        print("    Install with: pip install openevolve")
        return False
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("  ✗ OPENAI_API_KEY environment variable not set!")
        print("    Get a Gemini API key from: https://aistudio.google.com/apikey")
        print("    Then set: export OPENAI_API_KEY='your-api-key'")
        return False
    print("  ✓ API key configured")
    
    # Check if required files exist
    required_files = [
        "initial_program.py",
        "evaluator.py",
        "config.yaml",
        "system_prompt.txt"
    ]
    
    current_dir = Path(__file__).parent
    for file in required_files:
        file_path = current_dir / file
        if not file_path.exists():
            print(f"  ✗ Missing required file: {file}")
            return False
    print("  ✓ All required files present")
    
    # Check if DRAMsim3 is available
    dramsim_path = Path("/home/kamil/DRAMsim3/build/dramsim3main")
    if not dramsim_path.exists():
        print(f"  ✗ DRAMsim3 not found at {dramsim_path}")
        return False
    print("  ✓ DRAMsim3 available")
    
    return True


def print_banner():
    """Print startup banner."""
    print("=" * 70)
    print("🧬 OpenEvolve DRAM Timing Optimization")
    print("=" * 70)
    print()
    print("Methodology: ADRS (Automated Design via Repeated Sampling)")
    print("Target: DDR4-3200 timing parameter optimization")
    print("Parameters: CL, tRCD, tRP, tRAS")
    print("Workloads: Random access + Sequential streaming")
    print()


def estimate_cost_and_time(iterations):
    """Estimate the cost and time for the evolution run."""
    print(f"📊 Estimated resource requirements for {iterations} iterations:")
    print()
    
    # Cost estimation (using Gemini Flash pricing)
    cost_per_iter_low = 0.01
    cost_per_iter_high = 0.05
    total_cost_low = iterations * cost_per_iter_low
    total_cost_high = iterations * cost_per_iter_high
    
    print(f"  💰 Cost estimate: ${total_cost_low:.2f} - ${total_cost_high:.2f}")
    print(f"     (Using Gemini 2.0 Flash: ~$0.01-0.05 per iteration)")
    print()
    
    # Time estimation
    # Each iteration: ~45-90 seconds (LLM call + 2 simulations)
    time_per_iter_low = 45  # seconds
    time_per_iter_high = 90  # seconds
    total_time_low = (iterations * time_per_iter_low) / 60  # minutes
    total_time_high = (iterations * time_per_iter_high) / 60  # minutes
    
    print(f"  ⏱️  Time estimate: {total_time_low:.0f} - {total_time_high:.0f} minutes")
    print(f"     ({total_time_low/60:.1f} - {total_time_high/60:.1f} hours)")
    print()


def run_openevolve(iterations, resume):
    """Run OpenEvolve with the specified configuration."""
    current_dir = Path(__file__).parent
    
    print("🚀 Launching OpenEvolve...")
    print(f"   Initial program: {current_dir / 'initial_program.py'}")
    print(f"   Evaluator: {current_dir / 'evaluator.py'}")
    print(f"   Config: {current_dir / 'config.yaml'}")
    print(f"   Iterations: {iterations}")
    if resume:
        print("   Mode: RESUME from checkpoint")
    print()
    print("=" * 70)
    print()
    
    # Import OpenEvolve library
    try:
        from openevolve import run_evolution
    except ImportError:
        print("❌ Failed to import openevolve")
        print("   Install with: pip install openevolve")
        sys.exit(1)
    
    # Run evolution using library API
    try:
        result = run_evolution(
            initial_program=str(current_dir / "initial_program.py"),
            evaluator=str(current_dir / "evaluator.py"),
            config=str(current_dir / "config.yaml"),
            iterations=iterations,
            output_dir=str(current_dir / "openevolve_output"),
            cleanup=False  # Keep all files for analysis
        )
        
        # Store result for post-processing
        return result
        
    except KeyboardInterrupt:
        print("\n⚠️  Evolution interrupted by user")
        print("   Progress saved in openevolve_output/")
        print("   Resume with: python run_evolution.py --resume")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Evolution failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def print_next_steps():
    """Print information about what to do after evolution completes."""
    print()
    print("=" * 70)
    print("✅ Evolution Complete!")
    print("=" * 70)
    print()
    print("📁 Results saved in: openevolve_output/")
    print()
    print("Next steps:")
    print()
    print("1. 📊 Visualize evolution progress:")
    print("   python -m openevolve.scripts.visualizer")
    print()
    print("2. 🔍 Examine best configuration:")
    print("   Check openevolve_output/best_program.py")
    print()
    print("3. 📈 Analyze detailed metrics:")
    print("   Check openevolve_output/evolution_metrics.json")
    print()
    print("4. 🧪 Test best configuration:")
    print("   python -c 'from openevolve_output.best_program import evaluate_timing_configuration; print(evaluate_timing_configuration().get_params())'")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Run OpenEvolve DRAM timing optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_evolution.py                    # Run with default settings (80 iterations)
  python run_evolution.py --iterations 200   # Run with 200 iterations
  python run_evolution.py --resume           # Resume from checkpoint
  
For more information, see README.md
        """
    )
    
    parser.add_argument(
        "--iterations",
        type=int,
        default=80,
        help="Number of evolution iterations (default: 80)"
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from previous checkpoint"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Check prerequisites
    if not check_prerequisites():
        print()
        print("❌ Prerequisites not met. Please fix the issues above and try again.")
        sys.exit(1)
    
    print()
    print("✓ All prerequisites satisfied!")
    print()
    
    # Show estimates
    estimate_cost_and_time(args.iterations)
    
    # Confirm with user
    if not args.resume:
        try:
            response = input("Continue with evolution? [Y/n] ").strip().lower()
            if response and response not in ['y', 'yes']:
                print("Aborted.")
                sys.exit(0)
        except KeyboardInterrupt:
            print("\nAborted.")
            sys.exit(0)
        print()
    
    # Run evolution
    result = run_openevolve(args.iterations, args.resume)
    
    # Print results summary
    if result:
        print()
        print("=" * 70)
        print("📊 Evolution Results Summary")
        print("=" * 70)
        print(f"Best Score: {result.best_score:.4f}")
        print(f"Best Program: openevolve_output/best_program.py")
        print()
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()
