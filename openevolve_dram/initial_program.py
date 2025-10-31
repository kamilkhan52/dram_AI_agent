"""
Initial DRAM Timing Configuration Program

This is the baseline DDR4-3200 JEDEC timing configuration that OpenEvolve
will evolve to find optimal parameters.
"""

class TimingConfiguration:
    """
    DRAM timing configuration to be evolved by OpenEvolve.
    
    This class represents the "genome" that will be evolved. The LLM will
    modify the parameter values to optimize performance while maintaining
    timing constraints.
    """
    
    def __init__(self):
        """Initialize with DDR4-3200 JEDEC baseline timing parameters."""
        # These are the parameters that OpenEvolve will optimize
        self.CL = 22      # CAS Latency (cycles)
        self.tRCD = 22    # RAS to CAS Delay (cycles)
        self.tRP = 22     # Row Precharge (cycles)
        self.tRAS = 52    # Row Active Strobe (cycles)
    
    def get_params(self):
        """
        Return timing parameters as a dictionary.
        
        Returns:
            dict: Timing parameters for DRAMsim3 evaluation
        """
        return {
            'CL': self.CL,
            'tRCD': self.tRCD,
            'tRP': self.tRP,
            'tRAS': self.tRAS
        }
    
    def validate(self):
        """
        Validate timing constraints.
        
        Returns:
            tuple: (is_valid, error_message)
        """
        # Check that all parameters are positive integers
        params = self.get_params()
        for name, value in params.items():
            if not isinstance(value, int) or value <= 0:
                return False, f"{name} must be a positive integer, got {value}"
        
        # Check timing constraint: tRAS >= tRCD + CL
        if self.tRAS < (self.tRCD + self.CL):
            return False, f"Constraint violated: tRAS ({self.tRAS}) must be >= tRCD ({self.tRCD}) + CL ({self.CL}) = {self.tRCD + self.CL}"
        
        # Check parameter bounds (from JEDEC specifications)
        if not (10 <= self.CL <= 30):
            return False, f"CL must be in range [10, 30], got {self.CL}"
        if not (10 <= self.tRCD <= 30):
            return False, f"tRCD must be in range [10, 30], got {self.tRCD}"
        if not (10 <= self.tRP <= 30):
            return False, f"tRP must be in range [10, 30], got {self.tRP}"
        if not (25 <= self.tRAS <= 80):
            return False, f"tRAS must be in range [25, 80], got {self.tRAS}"
        
        return True, "Valid configuration"


def evaluate_timing_configuration():
    """
    Entry point function that OpenEvolve will call.
    
    Returns:
        TimingConfiguration: The timing configuration to be evaluated
    """
    return TimingConfiguration()
