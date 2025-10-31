# dramsim3_evaluator.py

import subprocess
import json
import os
import shutil
import time
from typing import Dict, List, Tuple
import copy

class DRAMsim3Evaluator:
    """
    Wrapper for DRAMsim3 to evaluate timing configurations.
    Handles config modification, simulation execution, and metric extraction.
    """
    
    def __init__(self, 
                 dramsim_path: str = "/home/kamil/DRAMsim3/build/dramsim3main",
                 base_config: str = "/home/kamil/DRAMsim3/configs/DDR4_8Gb_x8_3200.ini",
                 output_dir: str = "./eval_outputs",
                 verbose: bool = True):
        self.dramsim_path = dramsim_path
        self.base_config = base_config
        self.output_dir = output_dir
        self.verbose = verbose
        os.makedirs(output_dir, exist_ok=True)
        
        # Load baseline configuration
        self.baseline_config = self._parse_config(base_config)
        self.baseline_stats = {}  # Will compute on first evaluation
        
        if self.verbose:
            print(f"Initialized DRAMsim3 Evaluator")
            print(f"  Simulator: {dramsim_path}")
            print(f"  Base config: {base_config}")
            print(f"  Output dir: {output_dir}")
        
    def _parse_config(self, config_path: str) -> Dict:
        """Parse .ini config file into nested dictionary."""
        config = {}
        current_section = None
        
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#') or line.startswith(';'):
                    continue
                    
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1]
                    config[current_section] = {}
                elif '=' in line and current_section:
                    key, value = line.split('=', 1)
                    config[current_section][key.strip()] = value.strip()
        
        return config
    
    def _write_config(self, config: Dict, output_path: str):
        """Write configuration dictionary to .ini file."""
        with open(output_path, 'w') as f:
            for section, params in config.items():
                f.write(f"[{section}]\n")
                for key, value in params.items():
                    f.write(f"{key} = {value}\n")
                f.write("\n")
    
    def _modify_timing_params(self, base_config: Dict, 
                             timing_params: Dict[str, int]) -> Dict:
        """
        Create new config with modified timing parameters.
        Deep copy to avoid modifying original.
        """
        new_config = {}
        for section, params in base_config.items():
            new_config[section] = params.copy()
        
        # Update timing section with new parameters
        for param, value in timing_params.items():
            if param in new_config['timing']:
                new_config['timing'][param] = str(int(value))
        
        return new_config
    
    def _check_timing_constraints(self, params: Dict[str, int]) -> Tuple[bool, str]:
        """
        Verify DRAM timing constraints are satisfied.
        Returns (is_valid, error_message)
        """
        # Get current values (use baseline if parameter not specified)
        def get_param(name):
            if name in params:
                return params[name]
            return int(self.baseline_config['timing'].get(name, 0))
        
        CL = get_param('CL')
        tRCD = get_param('tRCD')
        tRP = get_param('tRP')
        tRAS = get_param('tRAS')
        
        # Constraint 1: tRAS >= tRCD + CL (simplified JEDEC constraint)
        # In reality, tRAS >= tRCD + burst_time, but CL is a good proxy
        if tRAS < (tRCD + CL):
            return False, (f"Constraint violated: tRAS ({tRAS}) must be >= "
                          f"tRCD ({tRCD}) + CL ({CL}) = {tRCD + CL}")
        
        # Constraint 2: All values must be positive integers
        for name, value in params.items():
            if not isinstance(value, int) or value <= 0:
                return False, f"Parameter {name} = {value} must be positive integer"
        
        # Constraint 3: Reasonable bounds based on DDR4 specs
        bounds = {
            'CL': (10, 30),
            'tRCD': (10, 30),
            'tRP': (10, 30),
            'tRAS': (25, 80),
        }
        
        for param, value in params.items():
            if param in bounds:
                min_val, max_val = bounds[param]
                if not (min_val <= value <= max_val):
                    return False, (f"Parameter {param} = {value} out of "
                                  f"reasonable range [{min_val}, {max_val}]")
        
        return True, ""
    
    def _run_simulation(self, config_path: str, 
                       workload: str, 
                       cycles: int = 100000,
                       run_id: str = None) -> Dict:
        """
        Run DRAMsim3 simulation and extract statistics from JSON output.
        
        Args:
            config_path: Path to .ini configuration file
            workload: Either 'random', 'stream', or path to trace file
            cycles: Number of cycles to simulate
            run_id: Unique identifier for this run (for output naming)
        
        Returns:
            Dictionary with simulation results or error information
        """
        if run_id is None:
            run_id = f"{workload}_{int(time.time())}"
        
        output_path = os.path.abspath(os.path.join(self.output_dir, run_id))
        os.makedirs(output_path, exist_ok=True)
        
        # Build command based on workload type (use absolute paths)
        if workload in ["random", "stream"]:
            cmd = [
                os.path.abspath(self.dramsim_path),
                os.path.abspath(config_path),
                "--stream", workload,
                "-c", str(cycles),
                "-o", output_path
            ]
        elif os.path.isfile(workload):
            # Trace file
            cmd = [
                os.path.abspath(self.dramsim_path),
                os.path.abspath(config_path),
                "-t", os.path.abspath(workload),
                "-c", str(cycles),
                "-o", output_path
            ]
        else:
            return {"error": f"Unknown workload type: {workload}"}
        
        # Run simulation
        try:
            if self.verbose:
                print(f"  Running: {' '.join(cmd)}")
            
            # DRAMsim3 outputs to current directory, so we need to run from output_path
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=300,  # 5 minute timeout per simulation
                cwd="/home/kamil/DRAMsim3"  # Run from DRAMsim3 dir to find libs
            )
            
            if result.returncode != 0:
                return {
                    "error": f"Simulation failed with return code {result.returncode}",
                    "stderr": result.stderr,
                    "stdout": result.stdout
                }
            
            # Parse output JSON (should now be in output_path)
            json_file = os.path.join(output_path, "dramsim3.json")
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    stats = json.load(f)
                
                # Extract channel 0 stats (assuming single channel)
                channel_stats = stats.get("0", {})
                
                return {
                    "success": True,
                    "raw_stats": channel_stats,
                    "output_path": output_path
                }
            else:
                return {
                    "error": "Output JSON not found",
                    "output_path": output_path
                }
                
        except subprocess.TimeoutExpired:
            return {"error": "Simulation timeout (>5 minutes)"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
    
    def _extract_metrics(self, raw_stats: Dict) -> Dict:
        """
        Extract key performance metrics from DRAMsim3 JSON output.
        
        Based on actual JSON structure:
        {
          "average_read_latency": float,
          "average_bandwidth": float,
          "average_power": float,
          "total_energy": float,
          "num_read_cmds": int,
          "num_write_cmds": int,
          "num_read_row_hits": int,
          "num_write_row_hits": int,
          ...
        }
        """
        if "error" in raw_stats:
            return {"error": raw_stats["error"]}
        
        metrics = {}
        
        # Primary metrics
        metrics['read_latency'] = raw_stats.get('average_read_latency', float('inf'))
        metrics['bandwidth'] = raw_stats.get('average_bandwidth', 0.0)
        metrics['power'] = raw_stats.get('average_power', float('inf'))
        metrics['total_energy'] = raw_stats.get('total_energy', float('inf'))
        
        # Command statistics
        metrics['num_reads'] = raw_stats.get('num_read_cmds', 0)
        metrics['num_writes'] = raw_stats.get('num_write_cmds', 0)
        metrics['num_activations'] = raw_stats.get('num_act_cmds', 0)
        metrics['num_precharges'] = raw_stats.get('num_pre_cmds', 0)
        
        # Row buffer efficiency
        read_hits = raw_stats.get('num_read_row_hits', 0)
        write_hits = raw_stats.get('num_write_row_hits', 0)
        total_hits = read_hits + write_hits
        total_accesses = metrics['num_reads'] + metrics['num_writes']
        
        metrics['row_hit_rate'] = (total_hits / total_accesses 
                                   if total_accesses > 0 else 0.0)
        
        # Derived metrics
        metrics['num_cycles'] = raw_stats.get('num_cycles', 0)
        metrics['energy_per_access'] = (metrics['total_energy'] / total_accesses 
                                       if total_accesses > 0 else float('inf'))
        
        return metrics
    
    def _compute_score(self, metrics: Dict, baseline_metrics: Dict) -> float:
        """
        Compute normalized performance score.
        
        Score components (higher is better):
        - Latency improvement: 40% weight
        - Bandwidth improvement: 40% weight  
        - Energy efficiency: 20% weight
        """
        if "error" in metrics:
            return -float('inf')
        
        # Normalize metrics relative to baseline (higher is better)
        latency_score = (baseline_metrics['read_latency'] / 
                        max(metrics['read_latency'], 1.0))
        
        bandwidth_score = (metrics['bandwidth'] / 
                          max(baseline_metrics['bandwidth'], 1.0))
        
        energy_score = (baseline_metrics['energy_per_access'] / 
                       max(metrics['energy_per_access'], 1.0))
        
        # Weighted combination
        total_score = (
            0.4 * latency_score + 
            0.4 * bandwidth_score + 
            0.2 * energy_score
        )
        
        return total_score
    
    def evaluate_config(self, 
                       timing_params: Dict[str, int],
                       workloads: List[str] = None,
                       cycles: int = 100000) -> Dict:
        """
        Evaluate a timing configuration across multiple workloads.
        
        Args:
            timing_params: Dict of timing parameter names to values
                          e.g., {'CL': 20, 'tRCD': 18, 'tRP': 18, 'tRAS': 45}
            workloads: List of workload types (default: ['random', 'stream'])
            cycles: Number of cycles per simulation
        
        Returns:
            {
                'score': float (higher is better, -inf for invalid),
                'valid': bool,
                'error_msg': str,
                'timing_params': dict,
                'workload_scores': dict,
                'workload_metrics': dict
            }
        """
        if workloads is None:
            workloads = ['random', 'stream']
        
        # Check timing constraints
        is_valid, error_msg = self._check_timing_constraints(timing_params)
        if not is_valid:
            if self.verbose:
                print(f"  ❌ Invalid configuration: {error_msg}")
            return {
                "score": -float('inf'),
                "valid": False,
                "error_msg": error_msg,
                "timing_params": timing_params,
                "workload_scores": {},
                "workload_metrics": {}
            }
        
        # Initialize baseline if needed
        if not self.baseline_stats:
            if self.verbose:
                print("Computing baseline statistics...")
            
            for workload in workloads:
                result = self._run_simulation(
                    self.base_config,
                    workload,
                    cycles,
                    run_id=f"baseline_{workload}"
                )
                
                if "error" in result:
                    return {
                        "score": -float('inf'),
                        "valid": False,
                        "error_msg": f"Baseline simulation failed: {result['error']}",
                        "timing_params": timing_params,
                        "workload_scores": {},
                        "workload_metrics": {}
                    }
                
                metrics = self._extract_metrics(result['raw_stats'])
                self.baseline_stats[workload] = metrics
                
                if self.verbose:
                    print(f"  Baseline {workload}:")
                    print(f"    Read latency: {metrics['read_latency']:.2f} cycles")
                    print(f"    Bandwidth: {metrics['bandwidth']:.2f} MB/s")
                    print(f"    Energy/access: {metrics['energy_per_access']:.2e} pJ")
        
        # Create modified config file
        new_config = self._modify_timing_params(self.baseline_config, timing_params)
        config_path = os.path.join(
            self.output_dir,
            f"config_{abs(hash(str(timing_params)))}.ini"
        )
        self._write_config(new_config, config_path)
        
        # Evaluate across workloads
        workload_scores = {}
        workload_metrics = {}
        
        for workload in workloads:
            result = self._run_simulation(
                config_path,
                workload,
                cycles,
                run_id=f"eval_{abs(hash(str(timing_params)))}_{workload}"
            )
            
            if "error" in result:
                if self.verbose:
                    print(f"  ❌ Simulation failed for {workload}: {result['error']}")
                return {
                    "score": -float('inf'),
                    "valid": False,
                    "error_msg": f"Simulation failed: {result['error']}",
                    "timing_params": timing_params,
                    "workload_scores": workload_scores,
                    "workload_metrics": workload_metrics
                }
            
            metrics = self._extract_metrics(result['raw_stats'])
            baseline_metrics = self.baseline_stats[workload]
            score = self._compute_score(metrics, baseline_metrics)
            
            workload_scores[workload] = score
            workload_metrics[workload] = metrics
            
            if self.verbose:
                print(f"  {workload}: score={score:.4f}")
                print(f"    Latency: {metrics['read_latency']:.2f} cycles "
                      f"({metrics['read_latency']/baseline_metrics['read_latency']:.2%})")
                print(f"    Bandwidth: {metrics['bandwidth']:.2f} MB/s "
                      f"({metrics['bandwidth']/baseline_metrics['bandwidth']:.2%})")
        
        # Compute overall score (geometric mean to prevent gaming single workload)
        import math
        scores = list(workload_scores.values())
        overall_score = math.exp(
            sum(math.log(max(s, 0.01)) for s in scores) / len(scores)
        )
        
        return {
            "score": overall_score,
            "valid": True,
            "error_msg": "",
            "timing_params": timing_params,
            "workload_scores": workload_scores,
            "workload_metrics": workload_metrics
        }
