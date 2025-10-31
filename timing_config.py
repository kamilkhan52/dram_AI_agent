# timing_config.py

class TimingConfiguration:
    """
    DRAM timing configuration to be evolved by ADRS.
    
    This class will be modified by the LLM during evolution.
    The get_params() method returns the timing parameters to evaluate.
    """
    
    def __init__(self):
        # Baseline DDR4-3200 timing parameters
        # These values will be modified during evolution
        
        self.CL = 22      # CAS Latency (cycles)
        self.tRCD = 22    # RAS to CAS Delay (cycles)
        self.tRP = 22     # Row Precharge time (cycles)
        self.tRAS = 52    # Row Active Strobe (cycles)
    
    def get_params(self) -> dict:
        """
        Return timing parameters as dictionary for evaluation.
        
        Returns:
            dict: {'CL': int, 'tRCD': int, 'tRP': int, 'tRAS': int}
        """
        return {
            'CL': int(self.CL),
            'tRCD': int(self.tRCD),
            'tRP': int(self.tRP),
            'tRAS': int(self.tRAS)
        }
    
    def validate(self) -> tuple:
        """
        Check if configuration satisfies DRAM timing constraints.
        
        Returns:
            (bool, str): (is_valid, error_message)
        """
        # Constraint 1: tRAS >= tRCD + CL
        if self.tRAS < (self.tRCD + self.CL):
            return False, (f"Constraint violated: tRAS ({self.tRAS}) must be >= "
                          f"tRCD ({self.tRCD}) + CL ({self.CL}) = {self.tRCD + self.CL}")
        
        # Constraint 2: All values must be positive integers
        params = [self.CL, self.tRCD, self.tRP, self.tRAS]
        if any(not isinstance(p, int) or p <= 0 for p in params):
            return False, "All timing parameters must be positive integers"
        
        # Constraint 3: Reasonable bounds (DDR4 specs)
        bounds = {
            'CL': (10, 30, self.CL),
            'tRCD': (10, 30, self.tRCD),
            'tRP': (10, 30, self.tRP),
            'tRAS': (25, 80, self.tRAS),
        }
        
        for param_name, (min_val, max_val, value) in bounds.items():
            if not (min_val <= value <= max_val):
                return False, (f"{param_name} = {value} out of valid range "
                              f"[{min_val}, {max_val}]")
        
        return True, ""

# This is the entry point for evaluation
def evaluate_timing_configuration():
    """
    Create a timing configuration and return parameters for evaluation.
    This function will be called by the ADRS evaluator.
    """
    config = TimingConfiguration()
    
    # Validate before returning
    is_valid, error_msg = config.validate()
    if not is_valid:
        raise ValueError(f"Invalid timing configuration: {error_msg}")
    
    return config.get_params()
