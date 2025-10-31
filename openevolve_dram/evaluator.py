"""
OpenEvolve Evaluator for DRAM Timing Optimization

This evaluator integrates with OpenEvolve to assess DRAM timing configurations
using DRAMsim3. It provides the fitness function that guides evolution.
"""

import sys
import os
import traceback
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dramsim3_evaluator import DRAMsim3Evaluator
from openevolve.evaluation_result import EvaluationResult


def evaluate(program_path: str) -> EvaluationResult:
    """
    Evaluate a DRAM timing configuration program.
    
    This function is called by OpenEvolve for each evolved program. It:
    1. Imports the evolved TimingConfiguration class
    2. Validates the timing constraints
    3. Runs DRAMsim3 simulations for both workloads
    4. Returns comprehensive metrics for OpenEvolve
    
    Args:
        program_path: Path to the evolved Python program
        
    Returns:
        EvaluationResult: Contains metrics, artifacts, and feedback
    """
    try:
        # Initialize the DRAMsim3 evaluator
        evaluator = DRAMsim3Evaluator(
            dramsim_path="/home/kamil/DRAMsim3/build/dramsim3main",
            base_config="/home/kamil/DRAMsim3/configs/DDR4_8Gb_x8_3200.ini",
            output_dir="./openevolve_dram/eval_outputs"
        )
        
        # Import the evolved program
        import importlib.util
        spec = importlib.util.spec_from_file_location("evolved_program", program_path)
        evolved_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(evolved_module)
        
        # Get the timing configuration
        config_instance = evolved_module.evaluate_timing_configuration()
        
        # Validate the configuration
        is_valid, validation_msg = config_instance.validate()
        
        if not is_valid:
            # Return failure metrics for invalid configurations
            return EvaluationResult(
                metrics={
                    "combined_score": 0.0,
                    "random_score": 0.0,
                    "stream_score": 0.0,
                    "overall_score": 0.0,
                    "latency_improvement": 0.0,
                    "bandwidth_improvement": 0.0,
                    "energy_efficiency": 0.0,
                    "constraint_valid": 0.0
                },
                artifacts={
                    "error": f"CONSTRAINT VIOLATION: {validation_msg}",
                    "stderr": validation_msg,
                    "params": str(config_instance.get_params()),
                    "status": "invalid"
                }
            )
        
        # Convert TimingConfiguration to dict for evaluator
        timing_params_dict = config_instance.get_params()
        
        # Evaluate the valid configuration
        result = evaluator.evaluate_config(timing_params_dict)
        
        # Check if evaluation failed
        if not result['valid']:
            return EvaluationResult(
                metrics={
                    "combined_score": 0.0,
                    "random_score": 0.0,
                    "stream_score": 0.0,
                    "overall_score": 0.0,
                    "latency_improvement": 0.0,
                    "bandwidth_improvement": 0.0,
                    "energy_efficiency": 0.0,
                    "constraint_valid": 0.0
                },
                artifacts={
                    "error": f"SIMULATION ERROR: {result['error_msg']}",
                    "stderr": result['error_msg'],
                    "params": str(timing_params_dict),
                    "status": "simulation_failed"
                }
            )
        
        # Extract metrics for OpenEvolve
        overall_score = result['score']
        random_score = result['workload_scores']['random']
        stream_score = result['workload_scores']['stream']
        
        # Calculate additional feature dimensions for MAP-Elites
        random_metrics = result['workload_metrics']['random']
        stream_metrics = result['workload_metrics']['stream']
        random_baseline = evaluator.baseline_stats['random']
        stream_baseline = evaluator.baseline_stats['stream']
        
        # Latency improvement (higher is better)
        random_latency_improvement = (
            random_baseline['read_latency'] / random_metrics['read_latency']
        )
        stream_latency_improvement = (
            stream_baseline['read_latency'] / stream_metrics['read_latency']
        )
        avg_latency_improvement = (random_latency_improvement + stream_latency_improvement) / 2
        
        # Bandwidth improvement (higher is better)
        random_bandwidth_improvement = (
            random_metrics['bandwidth'] / random_baseline['bandwidth']
        )
        stream_bandwidth_improvement = (
            stream_metrics['bandwidth'] / stream_baseline['bandwidth']
        )
        avg_bandwidth_improvement = (random_bandwidth_improvement + stream_bandwidth_improvement) / 2
        
        # Energy efficiency (lower energy per access is better, so invert)
        random_energy_efficiency = (
            random_baseline['energy_per_access'] / random_metrics['energy_per_access']
        )
        stream_energy_efficiency = (
            stream_baseline['energy_per_access'] / stream_metrics['energy_per_access']
        )
        avg_energy_efficiency = (random_energy_efficiency + stream_energy_efficiency) / 2
        
        # Build success message for artifacts
        params = timing_params_dict
        success_msg = f"""
✅ VALID CONFIGURATION EVALUATED
Parameters: CL={params['CL']}, tRCD={params['tRCD']}, tRP={params['tRP']}, tRAS={params['tRAS']}
Random workload score: {random_score:.4f}
Stream workload score: {stream_score:.4f}
Overall score: {overall_score:.4f}

Performance breakdown:
- Random: {random_metrics['read_latency']:.2f} cycles (baseline: {random_baseline['read_latency']:.2f})
- Stream: {stream_metrics['read_latency']:.2f} cycles (baseline: {stream_baseline['read_latency']:.2f})
- Bandwidth improvement: {(avg_bandwidth_improvement - 1) * 100:+.2f}%
- Energy efficiency: {(avg_energy_efficiency - 1) * 100:+.2f}%
"""
        
        # Return comprehensive evaluation result
        return EvaluationResult(
            metrics={
                # Primary score for OpenEvolve optimization
                "combined_score": overall_score,
                
                # Individual workload scores
                "random_score": random_score,
                "stream_score": stream_score,
                "overall_score": overall_score,
                
                # Feature dimensions for MAP-Elites diversity
                "latency_improvement": avg_latency_improvement,
                "bandwidth_improvement": avg_bandwidth_improvement,
                "energy_efficiency": avg_energy_efficiency,
                
                # Constraint satisfaction flag
                "constraint_valid": 1.0,
                
                # Additional metrics for analysis
                "random_latency": random_metrics['read_latency'],
                "stream_latency": stream_metrics['read_latency'],
                "random_bandwidth": random_metrics['bandwidth'],
                "stream_bandwidth": stream_metrics['bandwidth'],
            },
            artifacts={
                "stdout": success_msg,
                "params": str(params),
                "detailed_results": str(result),
                "status": "valid"
            }
        )
        
    except Exception as e:
        # Handle any unexpected errors
        error_trace = traceback.format_exc()
        return EvaluationResult(
            metrics={
                "combined_score": 0.0,
                "random_score": 0.0,
                "stream_score": 0.0,
                "overall_score": 0.0,
                "latency_improvement": 0.0,
                "bandwidth_improvement": 0.0,
                "energy_efficiency": 0.0,
                "constraint_valid": 0.0
            },
            artifacts={
                "error": f"EVALUATION ERROR: {str(e)}",
                "stderr": error_trace,
                "status": "error"
            }
        )
