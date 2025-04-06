# deadlock_core.py

import numpy as np
import networkx as nx

class Process:
    """Represents a process in the system."""
    
    def __init__(self, pid, max_resources, allocated_resources=None, needed_resources=None):
        """
        Initialize a process with its resource requirements.
        
        Args:
            pid: Process identifier
            max_resources: Maximum resources required by the process
            allocated_resources: Resources currently allocated to the process
            needed_resources: Resources still needed by the process
        """
        self.pid = pid
        self.max_resources = np.array(max_resources)
        
        if allocated_resources is None:
            self.allocated_resources = np.zeros_like(self.max_resources)
        else:
            self.allocated_resources = np.array(allocated_resources)
            
        if needed_resources is None:
            self.needed_resources = self.max_resources - self.allocated_resources
        else:
            self.needed_resources = np.array(needed_resources)
            
        self.finished = False
        self.waiting_time = 0
        self.execution_time = 0
        self.priority = 0  # Default priority
        self.remaining_time = 0  # For scheduling algorithms
        
    def __str__(self):
        return f"Process {self.pid}: Max={self.max_resources}, Allocated={self.allocated_resources}, Need={self.needed_resources}"


class ResourceManager:
    """Manages resources and deadlock detection in the system."""
    
    def __init__(self, available_resources, processes=None):
        """
        Initialize the resource manager.
        
        Args:
            available_resources: Total available resources in the system
            processes: List of processes in the system
        """
        self.available_resources = np.array(available_resources)
        self.processes = processes if processes is not None else []
        self.deadlock_processes = []
        
    def add_process(self, process):
        """Add a process to the system."""
        self.processes.append(process)
        
    def request_resources(self, pid, request):
        """
        Process resource request.
        
        Args:
            pid: Process identifier
            request: Resource request vector
            
        Returns:
            bool: True if request is granted, False otherwise
        """
        process = next((p for p in self.processes if p.pid == pid), None)
        if process is None:
            return False
            
        request = np.array(request)
        
        # Check if request is valid
        if np.any(request > process.needed_resources) or np.any(request > self.available_resources):
            return False
            
        # Temporarily allocate resources to check if safe
        self.available_resources -= request
        process.allocated_resources += request
        process.needed_resources -= request
        
        # Check if system is in safe state
        if self.is_safe():
            return True
        else:
            # Rollback changes
            self.available_resources += request
            process.allocated_resources -= request
            process.needed_resources += request
            return False
            
    def release_resources(self, pid, resources):
        """
        Process releases resources.
        
        Args:
            pid: Process identifier
            resources: Resource release vector
            
        Returns:
            bool: True if resources are released successfully
        """
        process = next((p for p in self.processes if p.pid == pid), None)
        if process is None:
            return False
            
        resources = np.array(resources)
        
        # Check if release is valid
        if np.any(resources > process.allocated_resources):
            return False
            
        # Update resource allocation
        self.available_resources += resources
        process.allocated_resources -= resources
        process.needed_resources += resources
        
        return True

    def resolve_deadlock_by_preemption(self):
        """
        Resolve deadlock by preempting resources from processes.

        Returns:
        list: Processes from which resources were preempted
        """
        # First, detect which processes are involved in the deadlock
        deadlocked_processes = self.detect_deadlock()

        if not deadlocked_processes:
            return []

        preempted_processes = []

    # Strategy: Preempt resources from deadlocked processes to break the cycle
        for process in deadlocked_processes:
            # Preempt some resources to allow other processes to proceed
            # Check if the process has any allocated resources
            if np.any(process.allocated_resources > 0):
            # Temporarily return all allocated resources to the available pool
                self.available_resources += process.allocated_resources
                process.needed_resources += process.allocated_resources
                process.allocated_resources = np.zeros_like(process.allocated_resources)

                preempted_processes.append(process)

        return preempted_processes    


    def is_safe(self):
        """
        Check if the system is in a safe state using the Banker's algorithm.
        
        Returns:
            bool: True if system is in safe state, False otherwise
        """
        # Create working copies
        work = np.copy(self.available_resources)
        finish = [False] * len(self.processes)
        
        # Find an unfinished process whose needs can be satisfied
        found = True
        while found:
            found = False
            for i, p in enumerate(self.processes):
                if not finish[i] and np.all(p.needed_resources <= work):
                    work += p.allocated_resources
                    finish[i] = True
                    found = True
                    
        # System is safe if all processes can finish
        return all(finish)
    
    # def detect_deadlock(self):
    #     """
    #     Detect deadlock using resource allocation graph.
        
    #     Returns:
    #         list: List of processes in deadlock
    #     """
    #     # Create working copies
    #     work = np.copy(self.available_resources)
    #     finish = [False] * len(self.processes)
        
    #     # Mark processes that can complete with available resources
    #     found = True
    #     while found:
    #         found = False
    #         for i, p in enumerate(self.processes):
    #             if not finish[i] and np.all(p.needed_resources <= work):
    #                 work += p.allocated_resources
    #                 finish[i] = True
    #                 found = True
        
    #     # Processes that cannot finish are in deadlock
    #     self.deadlock_processes = [p for i, p in enumerate(self.processes) if not finish[i]]
    #     return self.deadlock_processes

    def detect_deadlock(self):
   
    # Create a resource allocation graph
        graph = nx.DiGraph()
    
    # Add nodes for processes and resources
        for p in self.processes:
            graph.add_node(f"P{p.pid}", type="process")
            for i, alloc in enumerate(p.allocated_resources):
                if alloc > 0:
                    graph.add_node(f"R{i}", type="resource")
                    graph.add_edge(f"R{i}", f"P{p.pid}")  # Allocation edge

        # Add request edges
        for p in self.processes:
            for i, need in enumerate(p.needed_resources):
                if need > 0 and self.available_resources[i] < need:
                    if f"R{i}" in graph:
                        graph.add_edge(f"P{p.pid}", f"R{i}")  # Request edge

        # Find cycles in the graph
        try:
            cycle = nx.find_cycle(graph)
            self.deadlock_processes = [p for p in self.processes 
                                     if f"P{p.pid}" in {u for u,v in cycle}]
            return self.deadlock_processes
        except nx.NetworkXNoCycle:
            self.deadlock_processes = []
            return []

    def resolve_deadlock_by_termination(self):
        """
        Resolve deadlock by terminating processes.
        
        Returns:
            list: List of terminated processes
        """
        if not self.deadlock_processes:
            self.detect_deadlock()
            
        terminated = []
        
        # Sort deadlocked processes by resource usage (terminate those with most resources first)
        for p in sorted(self.deadlock_processes, key=lambda x: np.sum(x.allocated_resources), reverse=True):
            # Release resources
            self.available_resources += p.allocated_resources
            p.allocated_resources = np.zeros_like(p.allocated_resources)
            p.needed_resources = np.copy(p.max_resources)
            terminated.append(p)
            
            # Check if remaining deadlock is resolved
            if not self.detect_deadlock():
                break
                
        return terminated
    
    def resolve_deadlock_by_resource_preemption(self):
        """
        Resolve deadlock by preempting resources.
        
        Returns:
            dict: Mapping of processes to preempted resources
        """
        if not self.deadlock_processes:
            self.detect_deadlock()
            
        preempted = {}
        
        # Sort deadlocked processes by priority (if defined)
        for p in sorted(self.deadlock_processes, key=lambda x: x.priority):
            # Preempt resources in order of need
            resources_needed = np.minimum(p.allocated_resources, 1)  # Take at most 1 of each resource
            
            # Update resource allocation
            self.available_resources += resources_needed
            p.allocated_resources -= resources_needed
            p.needed_resources += resources_needed
            
            preempted[p.pid] = resources_needed
            
            # Check if deadlock is resolved
            if not self.detect_deadlock():
                break
                
        return preempted

    def get_resource_allocation_matrix(self):
        """
        Get the resource allocation matrix for visualization.
        
        Returns:
            dict: Contains allocation, max, need matrices and process IDs
        """
        n_processes = len(self.processes)
        n_resources = len(self.available_resources)
        
        allocation_matrix = np.zeros((n_processes, n_resources))
        max_matrix = np.zeros((n_processes, n_resources))
        need_matrix = np.zeros((n_processes, n_resources))
        pids = []
        
        for i, p in enumerate(self.processes):
            allocation_matrix[i] = p.allocated_resources
            max_matrix[i] = p.max_resources
            need_matrix[i] = p.needed_resources
            pids.append(p.pid)
            
        return {
            'allocation': allocation_matrix,
            'max': max_matrix,
            'need': need_matrix,
            'available': self.available_resources,
            'processes': pids
        }


# Predefined deadlock scenarios for simulation
# def create_deadlock_scenario(scenario_id):
#     """
#     Create a predefined deadlock scenario for simulation.
    
#     Args:
#         scenario_id: ID of the scenario to create
        
#     Returns:
#         ResourceManager: Initialized resource manager with the scenario
#     """
#     if scenario_id == 1:
#         # Classic deadlock with 4 processes and 3 resource types
#         manager = ResourceManager([3, 3, 2])
        
#         # Process 1 holds A and B, needs more B
#         p1 = Process(1, [5, 5, 3], [2, 1, 0], [3, 4, 3])
        
#         # Process 2 holds B and C, needs more A
#         p2 = Process(2, [2, 3, 5], [0, 1, 2], [2, 2, 3])
        
#         # Process 3 holds A and C, needs more B
#         p3 = Process(3, [1, 4, 2], [1, 0, 1], [0, 4, 1])
        
#         # Process 4 needs resources from other processes
#         p4 = Process(4, [3, 2, 4], [0, 1, 1], [3, 1, 3])
        
#         manager.add_process(p1)
#         manager.add_process(p2)
#         manager.add_process(p3)
#         manager.add_process(p4)
        
#         return manager
        
#     elif scenario_id == 2:
#         # Circular wait scenario
#         manager = ResourceManager([1, 1, 1])
        
#         # Process 1 holds A, needs B
#         p1 = Process(1, [1, 1, 0], [1, 0, 0], [0, 1, 0])
        
#         # Process 2 holds B, needs C
#         p2 = Process(2, [0, 1, 1], [0, 1, 0], [0, 0, 1])
        
#         # Process 3 holds C, needs A
#         p3 = Process(3, [1, 0, 1], [0, 0, 1], [1, 0, 0])
        
#         manager.add_process(p1)
#         manager.add_process(p2)
#         manager.add_process(p3)
        
#         return manager
        
#     elif scenario_id == 3:
#         # No deadlock scenario (safe state)
#         manager = ResourceManager([2, 1, 1])
        
#         p1 = Process(1, [2, 1, 0], [1, 0, 0], [1, 1, 0])
#         p2 = Process(2, [1, 1, 1], [0, 1, 0], [1, 0, 1])
#         p3 = Process(3, [1, 0, 2], [0, 0, 1], [1, 0, 1])
        
#         manager.add_process(p1)
#         manager.add_process(p2)
#         manager.add_process(p3)
        
#         return manager
        
#     elif scenario_id == 4:
#         # Deadlock with mutual exclusion and resource holding
#         manager = ResourceManager([1, 1])
        
#         p1 = Process(1, [1, 1], [1, 0], [0, 1])
#         p2 = Process(2, [1, 1], [0, 1], [1, 0])
        
#         manager.add_process(p1)
#         manager.add_process(p2)
        
#         return manager
        
#     elif scenario_id == 5:
#         # Complex scenario with multiple resource types
#         manager = ResourceManager([4, 3, 3, 2])
        
#         p1 = Process(1, [2, 1, 3, 1], [1, 1, 2, 0], [1, 0, 1, 1])
#         p2 = Process(2, [3, 1, 0, 2], [2, 0, 0, 1], [1, 1, 0, 1])
#         p3 = Process(3, [1, 3, 2, 1], [1, 2, 1, 0], [0, 1, 1, 1])
#         p4 = Process(4, [2, 1, 1, 2], [0, 0, 0, 1], [2, 1, 1, 1])
        
#         manager.add_process(p1)
#         manager.add_process(p2)
#         manager.add_process(p3)
#         manager.add_process(p4)
        
#         return manager
        
#     elif scenario_id == 6:
#         # Partial deadlock scenario
#         manager = ResourceManager([5, 5, 5])
        
#         p1 = Process(1, [3, 2, 1], [2, 1, 0], [1, 1, 1])
#         p2 = Process(2, [1, 3, 2], [1, 2, 1], [0, 1, 1])
#         p3 = Process(3, [2, 2, 3], [1, 1, 2], [1, 1, 1])
#         p4 = Process(4, [1, 1, 2], [0, 0, 1], [1, 1, 1])
#         p5 = Process(5, [3, 3, 3], [0, 0, 0], [3, 3, 3])  # Not in deadlock
        
#         manager.add_process(p1)
#         manager.add_process(p2)
#         manager.add_process(p3)
#         manager.add_process(p4)
#         manager.add_process(p5)
        
#         return manager
        
#     elif scenario_id == 7:
#         # Resource shortage deadlock
#         manager = ResourceManager([1, 1, 1])
        
#         p1 = Process(1, [2, 0, 0], [1, 0, 0], [1, 0, 0])
#         p2 = Process(2, [0, 2, 0], [0, 1, 0], [0, 1, 0])
#         p3 = Process(3, [0, 0, 2], [0, 0, 1], [0, 0, 1])
        
#         manager.add_process(p1)
#         manager.add_process(p2)
#         manager.add_process(p3)
        
#         return manager
        
#     elif scenario_id == 8:
#         # Complex resource request pattern
#         manager = ResourceManager([3, 2, 3, 1])
        
#         p1 = Process(1, [1, 1, 2, 0], [1, 1, 0, 0], [0, 0, 2, 0])
#         p2 = Process(2, [2, 0, 1, 1], [1, 0, 0, 1], [1, 0, 1, 0])
#         p3 = Process(3, [2, 1, 1, 0], [0, 0, 1, 0], [2, 1, 0, 0])
#         p4 = Process(4, [0, 2, 1, 0], [0, 1, 1, 0], [0, 1, 0, 0])
        
#         manager.add_process(p1)
#         manager.add_process(p2)
#         manager.add_process(p3)
#         manager.add_process(p4)
        
#         return manager
        
#     elif scenario_id == 9:
#         # Multi-instance resource deadlock
#         manager = ResourceManager([2, 2, 2])
        
#         p1 = Process(1, [2, 2, 2], [1, 0, 1], [1, 2, 1])
#         p2 = Process(2, [2, 2, 2], [1, 1, 0], [1, 1, 2])
#         p3 = Process(3, [2, 2, 2], [0, 1, 1], [2, 1, 1])
        
#         manager.add_process(p1)
#         manager.add_process(p2)
#         manager.add_process(p3)
        
#         return manager
        
#     else:
#         # Default simple deadlock
#         manager = ResourceManager([1, 1])
        
#         p1 = Process(1, [1, 1], [1, 0], [0, 1])
#         p2 = Process(2, [1, 1], [0, 1], [1, 0])
        
#         manager.add_process(p1)
#         manager.add_process(p2)
        
#         return manager

def create_deadlock_scenario(scenario_id):
    """Returns a guaranteed deadlock scenario for testing"""
    if scenario_id == 1:
        # Classic circular wait (3 processes)
        manager = ResourceManager([0, 0, 0])  # No available resources
        p1 = Process(1, [1, 0, 0], [1, 0, 0], [0, 1, 0])  # Holds R1, needs R2
        p2 = Process(2, [0, 1, 0], [0, 1, 0], [0, 0, 1])  # Holds R2, needs R3
        p3 = Process(3, [0, 0, 1], [0, 0, 1], [1, 0, 0])  # Holds R3, needs R1
        
    elif scenario_id == 2:
        # Simple mutual exclusion (2 processes)
        manager = ResourceManager([0, 0])
        p1 = Process(1, [1, 1], [1, 0], [0, 1])  # Holds R1, needs R2
        p2 = Process(2, [1, 1], [0, 1], [1, 0])  # Holds R2, needs R1
        
    elif scenario_id == 3:
        # 4-way circular wait
        manager = ResourceManager([0, 0, 0, 0])
        p1 = Process(1, [1, 0, 0, 0], [1, 0, 0, 0], [0, 1, 0, 0])
        p2 = Process(2, [0, 1, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0])
        p3 = Process(3, [0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 0, 1])
        p4 = Process(4, [0, 0, 0, 1], [0, 0, 0, 1], [1, 0, 0, 0])
        
    elif scenario_id == 4:
        # Partial deadlock (3 deadlocked + 1 free)
        manager = ResourceManager([0, 0, 0])
        p1 = Process(1, [1, 0, 0], [1, 0, 0], [0, 1, 0])  # Deadlocked
        p2 = Process(2, [0, 1, 0], [0, 1, 0], [0, 0, 1])  # Deadlocked
        p3 = Process(3, [0, 0, 1], [0, 0, 1], [1, 0, 0])  # Deadlocked
        p4 = Process(4, [0, 0, 0], [0, 0, 0], [0, 0, 1])  # Can complete
        
    elif scenario_id == 5:
        # Multi-resource deadlock (each process holds multiple resources)
        manager = ResourceManager([0, 0, 0, 0])
        p1 = Process(1, [1, 1, 0, 0], [1, 0, 0, 0], [0, 1, 0, 0])
        p2 = Process(2, [0, 1, 1, 0], [0, 1, 0, 0], [0, 0, 1, 0])
        p3 = Process(3, [0, 0, 1, 1], [0, 0, 1, 0], [0, 0, 0, 1])
        p4 = Process(4, [1, 0, 0, 1], [0, 0, 0, 1], [1, 0, 0, 0])
        
    elif scenario_id == 6:
    # Starvation-like deadlock - all processes waiting for one resource
        manager = ResourceManager([0, 0])  # No resources available at all
        p1 = Process(1, [0, 1], [0, 0], [0, 1])  # Needs R2
        p2 = Process(2, [0, 1], [0, 0], [0, 1])  # Needs R2 
        p3 = Process(3, [1, 0], [1, 0], [0, 1])  # Holds R1, needs R2
        p4 = Process(4, [1, 0], [1, 0], [0, 1])  # Holds R1, needs R2
        
    elif scenario_id == 7:
        # Complex nested deadlock
        manager = ResourceManager([0, 0, 0, 0, 0])
        p1 = Process(1, [1, 0, 0, 0, 0], [1, 0, 0, 0, 0], [0, 1, 0, 0, 0])
        p2 = Process(2, [0, 1, 0, 0, 0], [0, 1, 0, 0, 0], [0, 0, 1, 1, 0])
        p3 = Process(3, [0, 0, 1, 0, 0], [0, 0, 1, 0, 0], [1, 0, 0, 0, 1])
        p4 = Process(4, [0, 0, 0, 1, 0], [0, 0, 0, 1, 0], [0, 0, 0, 0, 1])
        p5 = Process(5, [0, 0, 0, 0, 1], [0, 0, 0, 0, 1], [0, 1, 0, 0, 0])
        
    elif scenario_id == 8:
        # Mixed single/multi-instance deadlock
        manager = ResourceManager([0, 0, 0])  # R1 single, R2/R3 multi
        p1 = Process(1, [1, 2, 0], [1, 0, 0], [0, 2, 1])  # Holds R1, needs R2/R3
        p2 = Process(2, [0, 2, 1], [0, 2, 0], [1, 0, 1])  # Holds R2, needs R1/R3
        p3 = Process(3, [1, 0, 2], [0, 0, 2], [1, 1, 0])  # Holds R3, needs R1/R2
        
    elif scenario_id == 9:
        # Large-scale deadlock (6 processes)
        manager = ResourceManager([0]*6)  # 6 resources
        p1 = Process(1, [1,0,0,0,0,0], [1,0,0,0,0,0], [0,1,0,0,0,0])
        p2 = Process(2, [0,1,0,0,0,0], [0,1,0,0,0,0], [0,0,1,0,0,0])
        p3 = Process(3, [0,0,1,0,0,0], [0,0,1,0,0,0], [0,0,0,1,0,0])
        p4 = Process(4, [0,0,0,1,0,0], [0,0,0,1,0,0], [0,0,0,0,1,0])
        p5 = Process(5, [0,0,0,0,1,0], [0,0,0,0,1,0], [0,0,0,0,0,1])
        p6 = Process(6, [0,0,0,0,0,1], [0,0,0,0,0,1], [1,0,0,0,0,0])
        
    else:
        raise ValueError("Invalid scenario ID")

    # Add all processes to manager
    processes = [p for p in locals().values() if isinstance(p, Process)]
    for p in processes:
        manager.add_process(p)
    
    return manager