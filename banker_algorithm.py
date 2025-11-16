"""
Banker's Algorithm Implementation for Deadlock Prevention
Predicts if system will be in safe state before granting resources
"""

class BankerAlgorithm:
    """
    Implements Banker's Algorithm for deadlock avoidance
    """
    
    def __init__(self):
        self.processes = {}
        self.resources = {}
        self.max_need = {}  # Maximum resources each process might need
        self.allocation = {}  # Currently allocated resources
        self.need = {}  # Remaining need for each process
        self.available = {}  # Available resources
    
    def initialize(self, processes, resources):
        """Initialize Banker's Algorithm with processes and resources"""
        self.processes = processes
        self.resources = resources
        
        # Initialize matrices
        for proc_id in processes:
            self.allocation[proc_id] = {}
            self.need[proc_id] = {}
            self.max_need[proc_id] = {}
            
            for res_id in resources:
                self.allocation[proc_id][res_id] = 0
                self.max_need[proc_id][res_id] = resources[res_id].get('instances', 1)
                self.need[proc_id][res_id] = self.max_need[proc_id][res_id]
        
        # Initialize available resources
        self.available = {}
        for res_id, resource in resources.items():
            self.available[res_id] = resource.get('instances', 1)
    
    def update_allocation(self, process_id, resource_id, amount=1):
        """Update allocation when resource is allocated to process"""
        if process_id not in self.allocation or resource_id not in self.allocation[process_id]:
            return False
        
        self.allocation[process_id][resource_id] += amount
        self.need[process_id][resource_id] = max(0, self.need[process_id][resource_id] - amount)
        self.available[resource_id] = max(0, self.available[resource_id] - amount)
        return True
    
    def check_safe_state(self):
        """
        Check if system is in safe state using Banker's Algorithm
        Returns: (is_safe, safe_sequence, details)
        """
        # Make copies for simulation
        work = self.available.copy()
        finish = {proc_id: False for proc_id in self.processes}
        safe_sequence = []
        
        # Try to find safe sequence
        iterations = 0
        max_iterations = len(self.processes) * 2
        
        while len(safe_sequence) < len(self.processes) and iterations < max_iterations:
            iterations += 1
            found = False
            
            for proc_id in self.processes:
                if finish[proc_id]:
                    continue
                
                # Check if process can finish with available resources
                can_finish = True
                for res_id in self.resources:
                    if self.need[proc_id][res_id] > work.get(res_id, 0):
                        can_finish = False
                        break
                
                if can_finish:
                    # Process can finish, release its resources
                    for res_id in self.resources:
                        work[res_id] = work.get(res_id, 0) + self.allocation[proc_id][res_id]
                    
                    finish[proc_id] = True
                    safe_sequence.append(proc_id)
                    found = True
                    break
            
            if not found:
                break
        
        is_safe = len(safe_sequence) == len(self.processes)
        
        # Generate detailed explanation
        details = self._generate_safe_state_details(is_safe, safe_sequence, work)
        
        return is_safe, safe_sequence, details
    
    def predict_allocation(self, process_id, resource_id, amount=1):
        """
        Predict if allocating resource would keep system in safe state
        Returns: (is_safe, message, safe_sequence)
        """
        # Check if request exceeds need
        if self.need.get(process_id, {}).get(resource_id, 0) < amount:
            return False, f"Request exceeds maximum need for {process_id}", []
        
        # Check if resources are available
        if self.available.get(resource_id, 0) < amount:
            return False, f"Insufficient resources available. Need {amount}, have {self.available.get(resource_id, 0)}", []
        
        # Simulate allocation
        old_allocation = self.allocation[process_id][resource_id]
        old_need = self.need[process_id][resource_id]
        old_available = self.available[resource_id]
        
        # Temporarily allocate
        self.allocation[process_id][resource_id] += amount
        self.need[process_id][resource_id] -= amount
        self.available[resource_id] -= amount
        
        # Check if still in safe state
        is_safe, safe_sequence, details = self.check_safe_state()
        
        # Restore original state
        self.allocation[process_id][resource_id] = old_allocation
        self.need[process_id][resource_id] = old_need
        self.available[resource_id] = old_available
        
        if is_safe:
            return True, f"✅ Safe to allocate! System remains in safe state. Safe sequence: {' → '.join(safe_sequence)}", safe_sequence
        else:
            return False, f"⚠️ UNSAFE! Allocating would lead to potential deadlock. Request denied.", []
    
    def _generate_safe_state_details(self, is_safe, safe_sequence, final_work):
        """Generate detailed explanation of safe state check"""
        details = {
            'is_safe': is_safe,
            'safe_sequence': safe_sequence,
            'final_available': final_work,
            'allocation_matrix': self.allocation,
            'need_matrix': self.need,
            'available': self.available
        }
        return details
    
    def calculate_risk_score(self, process_id):
        """
        Calculate risk score for a process (0-100)
        Higher score = higher risk of causing deadlock
        """
        if process_id not in self.processes:
            return 0
        
        risk = 0
        
        # Factor 1: How many resources allocated (30 points)
        total_allocated = sum(self.allocation[process_id].values())
        max_possible = len(self.resources) * 2
        risk += (total_allocated / max(max_possible, 1)) * 30
        
        # Factor 2: How much more does it need (40 points)
        total_need = sum(self.need[process_id].values())
        risk += (total_need / max(max_possible, 1)) * 40
        
        # Factor 3: Resource availability (30 points)
        total_available = sum(self.available.values())
        if total_available < total_need:
            risk += 30
        else:
            risk += (1 - (total_available - total_need) / max(total_available, 1)) * 30
        
        return min(100, int(risk))
    
    def get_system_state(self):
        """Get complete system state for visualization"""
        is_safe, safe_sequence, details = self.check_safe_state()
        
        # Calculate risk scores for all processes
        risk_scores = {}
        for proc_id in self.processes:
            risk_scores[proc_id] = self.calculate_risk_score(proc_id)
        
        return {
            'is_safe': is_safe,
            'safe_sequence': safe_sequence,
            'details': details,
            'risk_scores': risk_scores,
            'available': self.available,
            'total_resources': {res_id: res['instances'] for res_id, res in self.resources.items()}
        }
