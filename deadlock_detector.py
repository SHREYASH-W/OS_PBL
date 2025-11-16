from banker_algorithm import BankerAlgorithm

class DeadlockDetector:
    """
    Deadlock detection algorithms implement karta hai:
    - Resource Allocation Graph (RAG) aur cycle detection
    - Banker's Algorithm (future enhancement ke liye)
    """
    
    def __init__(self):
        self.processes = {}  # {process_id: {name, allocated, requested}} — process ka data
        self.resources = {}  # {resource_id: {name, instances, available}} — resource ka data
        self.allocation = {}  # {process_id: [resource_ids]} — allocation mapping
        self.request = {}     # {process_id: [resource_ids]} — request mapping
        self.edges = []       # [(from, to, type)] — graph visualization ke liye edges
        self.banker = BankerAlgorithm()  # Banker's Algorithm prediction ke liye
    
    def reset(self):
        """Sab data structures ko reset karo"""
        self.processes = {}
        self.resources = {}
        self.allocation = {}
        self.request = {}
        self.edges = []
    
    def add_process(self, process_id, process_name):
        """Naya process add karo"""
        self.processes[process_id] = {
            'id': process_id,
            'name': process_name,
            'allocated': [],
            'requested': []
        }
        self.allocation[process_id] = []
        self.request[process_id] = []
        
        # Update Banker's Algorithm
        if len(self.resources) > 0:
            # Agar resources present hain toh Banker ko initialize karo
            self.banker.initialize(self.processes, self.resources)
    
    def add_resource(self, resource_id, resource_name, instances=1):
        """Naya resource add karo"""
        self.resources[resource_id] = {
            'id': resource_id,
            'name': resource_name,
            'instances': instances,
            'available': instances
        }
        
        # Update Banker's Algorithm
        if len(self.processes) > 0:
            # Agar processes already hain toh Banker ko initialize karo
            self.banker.initialize(self.processes, self.resources)
    
    def allocate_resource(self, process_id, resource_id):
        """Resource ko process ko allocate karo"""
        if process_id not in self.processes or resource_id not in self.resources:
            return False
        
        if self.resources[resource_id]['available'] > 0:
            self.allocation[process_id].append(resource_id)
            self.processes[process_id]['allocated'].append(resource_id)
            self.resources[resource_id]['available'] -= 1
            
            # Banker's Algorithm ko update karo
            self.banker.update_allocation(process_id, resource_id, 1)
            
            # Edge add karo: Resource -> Process (allocation)
            self.edges.append((resource_id, process_id, 'allocation'))
            return True
        return False
    
    def request_resource(self, process_id, resource_id):
        """Process resource request karega"""
        if process_id not in self.processes or resource_id not in self.resources:
            return False
        
        self.request[process_id].append(resource_id)
        self.processes[process_id]['requested'].append(resource_id)
        
        # Edge add karo: Process -> Resource (request)
        self.edges.append((process_id, resource_id, 'request'))
        return True
    
    def detect_deadlock(self):
        """
        RAG me cycle detect karke deadlock detect karo
        DFS use karke graph me cycles dhundo
        """
        # Build adjacency list for the graph
        graph = {}
        all_nodes = set(self.processes.keys()) | set(self.resources.keys())
        
        for node in all_nodes:
            graph[node] = []
        
        # Graph build kar rahe hain:
        # 1. Process -> Resource (request edge): Process resource ka wait kar raha hai
        # 2. Resource -> Process (allocation edge): Resource kisi process ke paas hai
        for process_id in self.processes:
            # Request edges: Process -> Resource
            for resource_id in self.request[process_id]:
                graph[process_id].append(resource_id)
            
            # Allocation edges: Resource -> Process (reverse direction)
            for resource_id in self.allocation[process_id]:
                graph[resource_id].append(process_id)
        
        # DFS se cycle detect karne ka function
        def has_cycle_dfs(node, visited, rec_stack, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    result = has_cycle_dfs(neighbor, visited, rec_stack, path)
                    if result:  # Agar cycle mil gayi toh upar propagate karo
                        return result
                elif neighbor in rec_stack:
                    # Cycle detect hui! Cycle nikal lo
                    cycle_start_idx = path.index(neighbor)
                    cycle = path[cycle_start_idx:] + [neighbor]
                    return cycle
            
            path.pop()
            rec_stack.remove(node)
            return None
        
        # Sab nodes ko check karo cycles ke liye
        visited = set()
        for node in all_nodes:
            if node not in visited:
                rec_stack = set()
                path = []
                cycle = has_cycle_dfs(node, visited, rec_stack, path)
                if cycle:
                    # Deadlock me involved processes nikal lo
                    deadlock_processes = [n for n in cycle if n in self.processes]
                    cycle_str = ' → '.join([str(n) for n in cycle])
                    
                    return {
                        'deadlock_detected': True,
                        'deadlock_cycle': cycle,
                        'deadlock_processes': deadlock_processes,
                        'message': f'Deadlock detected! Cycle: {cycle_str}'
                    }
        
        return {
            'deadlock_detected': False,
            'deadlock_cycle': [],
            'deadlock_processes': [],
            'message': 'No deadlock detected. System is in safe state.'
        }
    
    def remove_process(self, process_id):
        """Process remove karo (recovery simulation ke liye)"""
        if process_id in self.processes:
            # Is process ke paas jo resources hain unko release karo
            for resource_id in self.allocation.get(process_id, []):
                if resource_id in self.resources:
                    self.resources[resource_id]['available'] += 1
            
            # Process se related edges hata do
            self.edges = [edge for edge in self.edges if edge[0] != process_id and edge[1] != process_id]
            
            # Data structures se remove karo
            del self.processes[process_id]
            del self.allocation[process_id]
            del self.request[process_id]
            
            # Banker ko dobara initialize karo agar kuch processes/resources bache hain
            if len(self.processes) > 0 and len(self.resources) > 0:
                self.banker.initialize(self.processes, self.resources)
            
            return True
        return False
    
    def predict_deadlock(self):
        """
        Banker's Algorithm se predict karo ki system safe hai ya nahi
        Returns prediction analysis
        """
        if len(self.processes) == 0 or len(self.resources) == 0:
            return {
                'is_safe': True,
                'message': 'No processes or resources to analyze',
                'safe_sequence': [],
                'risk_level': 'low'
            }
        
        # Banker's Algorithm se system state lo
        state = self.banker.get_system_state()
        
        if state['is_safe']:
            return {
                'is_safe': True,
                'message': f"✅ System is in SAFE state. Safe sequence exists: {' → '.join(state['safe_sequence'])}",
                'safe_sequence': state['safe_sequence'],
                'risk_level': 'low',
                'risk_scores': state['risk_scores'],
                'details': state['details']
            }
        else:
            return {
                'is_safe': False,
                'message': '⚠️ System is in UNSAFE state! Deadlock may occur.',
                'safe_sequence': [],
                'risk_level': 'high',
                'risk_scores': state['risk_scores'],
                'details': state['details']
            }
    
    def predict_allocation(self, process_id, resource_id):
        """
        Predict karo agar resource allocate kiya toh safe rahega ya nahi
        """
        is_safe, message, safe_sequence = self.banker.predict_allocation(process_id, resource_id, 1)
        
        return {
            'is_safe': is_safe,
            'message': message,
            'safe_sequence': safe_sequence,
            'risk_level': 'low' if is_safe else 'high'
        }
    
    def get_processes(self):
        """Sab processes lo"""
        return list(self.processes.values())
    
    def get_resources(self):
        """Sab resources lo"""
        return list(self.resources.values())
    
    def get_graph_data(self):
        """Visualization ke liye graph data do"""
        nodes = []
        links = []
        
        # Process nodes add karo
        for pid, process in self.processes.items():
            nodes.append({
                'id': pid,
                'label': process['name'],
                'type': 'process'
            })
        
        # Resource nodes add karo
        for rid, resource in self.resources.items():
            nodes.append({
                'id': rid,
                'label': resource['name'],
                'type': 'resource',
                'instances': resource['instances']
            })
        
        # Edges add karo
        for edge in self.edges:
            from_node, to_node, edge_type = edge
            links.append({
                'source': from_node,
                'target': to_node,
                'type': edge_type
            })
        
        return {'nodes': nodes, 'links': links}
