# test_setup.py

"""
Test script to validate the complete ADRS setup before running evolution.
"""

import sys
import os
from dramsim3_evaluator import DRAMsim3Evaluator
from timing_config import TimingConfiguration, evaluate_timing_configuration

def test_evaluator():
    """Test that the evaluator works correctly."""
    print("=" * 70)
    print("TEST 1: DRAMsim3 Evaluator")
    print("=" * 70)
    
    evaluator = DRAMsim3Evaluator(
        dramsim_path="/home/kamil/DRAMsim3/build/dramsim3main",
        base_config="/home/kamil/DRAMsim3/configs/DDR4_8Gb_x8_3200.ini",
        output_dir="./test_outputs",
        verbose=True
    )
    
    # Test baseline evaluation
    print("\nTesting baseline configuration...")
    baseline_params = {'CL': 22, 'tRCD': 22, 'tRP': 22, 'tRAS': 52}
    result = evaluator.evaluate_config(
        baseline_params,
        workloads=['random'],
        cycles=100000
    )
    
    if result['valid'] and abs(result['score'] - 1.0) < 0.01:
        print("✓ Baseline test passed (score ≈ 1.0)")
        return evaluator
    else:
        print(f"✗ Baseline test failed (score = {result['score']:.4f}, expected ≈ 1.0)")
        return None

def test_configuration_class():
    """Test the TimingConfiguration class."""
    print("\n" + "=" * 70)
    print("TEST 2: TimingConfiguration Class")
    print("=" * 70)
    
    # Test valid configuration
    config = TimingConfiguration()
    is_valid, msg = config.validate()
    
    if is_valid:
        print("✓ Default configuration is valid")
        print(f"  Parameters: {config.get_params()}")
    else:
        print(f"✗ Default configuration invalid: {msg}")
        return False
    
    # Test constraint violation
    config.tRAS = 30  # This should violate tRAS >= tRCD + CL
    is_valid, msg = config.validate()
    
    if not is_valid and "Constraint violated" in msg:
        print("✓ Constraint validation working correctly")
        print(f"  Caught: {msg}")
    else:
        print("✗ Constraint validation failed")
        return False
    
    return True

def test_end_to_end():
    """Test complete evaluation pipeline."""
    print("\n" + "=" * 70)
    print("TEST 3: End-to-End Evaluation")
    print("=" * 70)
    
    evaluator = DRAMsim3Evaluator(
        dramsim_path="/home/kamil/DRAMsim3/build/dramsim3main",
        base_config="/home/kamil/DRAMsim3/configs/DDR4_8Gb_x8_3200.ini",
        output_dir="./test_outputs",
        verbose=True
    )
    
    # Test a slightly modified configuration
    print("\nTesting modified configuration (more aggressive timing)...")
    test_params = {'CL': 20, 'tRCD': 20, 'tRP': 20, 'tRAS': 45}
    
    result = evaluator.evaluate_config(
        test_params,
        workloads=['random', 'stream'],
        cycles=100000
    )
    
    if result['valid']:
        print(f"\n✓ Modified configuration evaluated successfully")
        print(f"  Overall score: {result['score']:.4f}")
        print(f"  Workload scores:")
        for workload, score in result['workload_scores'].items():
            print(f"    {workload}: {score:.4f}")
        
        # Check if we got improvement
        if result['score'] > 1.0:
            print(f"  🎉 Found {(result['score']-1)*100:.1f}% improvement!")
        else:
            print(f"  ⚠ Performance decreased by {(1-result['score'])*100:.1f}%")
        
        return True
    else:
        print(f"✗ Evaluation failed: {result['error_msg']}")
        return False

def test_constraint_boundaries():
    """Test configurations at constraint boundaries."""
    print("\n" + "=" * 70)
    print("TEST 4: Constraint Boundary Testing")
    print("=" * 70)
    
    evaluator = DRAMsim3Evaluator(
        dramsim_path="/home/kamil/DRAMsim3/build/dramsim3main",
        base_config="/home/kamil/DRAMsim3/configs/DDR4_8Gb_x8_3200.ini",
        output_dir="./test_outputs",
        verbose=False
    )
    
    test_cases = [
        # (params, should_be_valid, description)
        ({'CL': 20, 'tRCD': 20, 'tRP': 20, 'tRAS': 40}, True, "Minimal valid tRAS"),
        ({'CL': 20, 'tRCD': 20, 'tRP': 20, 'tRAS': 39}, False, "tRAS too small"),
        ({'CL': 14, 'tRCD': 14, 'tRP': 14, 'tRAS': 35}, True, "Aggressive but valid"),
        ({'CL': 9, 'tRCD': 14, 'tRP': 14, 'tRAS': 35}, False, "CL below minimum"),
        ({'CL': 28, 'tRCD': 28, 'tRP': 28, 'tRAS': 70}, True, "Conservative max"),
        ({'CL': 31, 'tRCD': 28, 'tRP': 28, 'tRAS': 70}, False, "CL above maximum"),
    ]
    
    passed = 0
    for params, should_be_valid, description in test_cases:
        result = evaluator.evaluate_config(params, workloads=['random'], cycles=10000)
        
        if result['valid'] == should_be_valid:
            print(f"✓ {description}: {'Valid' if should_be_valid else 'Invalid'} as expected")
            passed += 1
        else:
            print(f"✗ {description}: Expected {'valid' if should_be_valid else 'invalid'}, "
                  f"got {'valid' if result['valid'] else 'invalid'}")
            if not result['valid']:
                print(f"  Error: {result['error_msg']}")
    
    print(f"\nPassed {passed}/{len(test_cases)} boundary tests")
    return passed == len(test_cases)

def main():
    """Run all tests."""
    print("\n" + "🧪" * 35)
    print("DRAM Timing Optimizer - Setup Validation")
    print("🧪" * 35 + "\n")
    
    tests = [
        ("Evaluator Initialization", test_evaluator),
        ("Configuration Class", test_configuration_class),
        ("End-to-End Pipeline", test_end_to_end),
        ("Constraint Boundaries", test_constraint_boundaries),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result is not False and result is not None))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! Ready to run ADRS optimization.")
        print("\nNext steps:")
        print("  1. Run manual parameter sweep: python manual_sweep.py")
        print("  2. Analyze results to understand parameter space")
        print("  3. Configure OpenEvolve with the provided prompt")
        print("  4. Run ADRS evolution for 80 iterations")
    else:
        print("\n⚠ Some tests failed. Please fix issues before proceeding.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
