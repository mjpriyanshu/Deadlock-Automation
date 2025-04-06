import numpy as np
from deadlock_core import Process, ResourceManager
import heapq
from collections import deque

class Scheduler:
    """Base class for different scheduling algorithms."""
    
    def __init__(self, processes=None):
        self.processes = processes if processes is not None else []
        self.time = 0
        self.running_process = None
        self.ready_queue = []
        self.completed_processes = []
        self.history = []
        
        # Initialize process states
        for p in self.processes:
            p.remaining_time = getattr(p, 'burst_time', 10)  # Default burst time
            p.waiting_time = 0
            p.execution_time = 0
            
    def add_process(self, process):
        """Add a process with proper initialization"""
        process.remaining_time = getattr(process, 'burst_time', 10)
        process.waiting_time = 0
        process.execution_time = 0
        self.processes.append(process)
        
    def is_complete(self):
        """Check if all processes are complete."""
        return len(self.completed_processes) == len(self.processes)
        
    def update_waiting_times(self):
        """Update waiting times for processes in ready queue"""
        for p in self.ready_queue:
            p.waiting_time += 1
            
    def step(self):
        """Base step implementation"""
        self.time += 1
        return False
        
    def run_simulation(self, max_steps=1000):
        """Run the complete scheduling simulation."""
        while not self.is_complete() and self.time < max_steps:
            self.step()
        return self.history

class FCFSScheduler(Scheduler):
    """First-Come, First-Served scheduler."""
    
    def __init__(self, processes=None):
        super().__init__(processes)
        # Initialize ready queue sorted by arrival time
        self.ready_queue = deque(sorted(self.processes, 
                                     key=lambda p: getattr(p, 'arrival_time', 0)))
        
    def step(self):
        if self.running_process is None and self.ready_queue:
            self.running_process = self.ready_queue.popleft()
            
        if self.running_process:
            # Execute the process
            self.running_process.remaining_time -= 1
            self.running_process.execution_time += 1
            
            # Update waiting times for other processes
            self.update_waiting_times()
            
            # Record history
            self.history.append({
                'time': self.time,
                'running': self.running_process.pid,
                'ready_queue': [p.pid for p in self.ready_queue],
                'completed': [p.pid for p in self.completed_processes]
            })
            
            # Check if process completed
            if self.running_process.remaining_time <= 0:
                self.completed_processes.append(self.running_process)
                self.running_process = None
                
        super().step()

class RoundRobinScheduler(Scheduler):
    """Round Robin scheduler with time quantum."""
    
    def __init__(self, processes=None, time_quantum=2):
        super().__init__(processes)
        self.ready_queue = deque(self.processes)
        self.time_quantum = time_quantum
        self.current_quantum = 0
        
    def step(self):
        if self.running_process is None and self.ready_queue:
            self.running_process = self.ready_queue.popleft()
            self.current_quantum = 0
            
        if self.running_process:
            # Execute the process
            self.running_process.remaining_time -= 1
            self.running_process.execution_time += 1
            self.current_quantum += 1
            
            # Update waiting times
            self.update_waiting_times()
            
            # Record history
            self.history.append({
                'time': self.time,
                'running': self.running_process.pid,
                'ready_queue': [p.pid for p in self.ready_queue],
                'completed': [p.pid for p in self.completed_processes],
                'quantum': self.current_quantum
            })
            
            # Check completion or quantum expiration
            if self.running_process.remaining_time <= 0:
                self.completed_processes.append(self.running_process)
                self.running_process = None
            elif self.current_quantum >= self.time_quantum:
                self.ready_queue.append(self.running_process)
                self.running_process = None
                
        super().step()

class BankersScheduler(Scheduler):
    """Banker's algorithm for deadlock avoidance."""
    
    def __init__(self, resource_manager, processes=None):
        super().__init__(processes)
        self.resource_manager = resource_manager
        self.ready_queue = deque(self.processes)
        
    def is_safe(self, process):
        """Check if allocating resources would leave system in safe state"""
        # Simulate allocation
        work = self.resource_manager.available_resources - process.needed_resources
        if np.any(work < 0):
            return False
            
        # Check if remaining processes can complete
        temp_processes = [p for p in self.ready_queue if p != process]
        return all(np.all(p.needed_resources <= work) for p in temp_processes)
        
    def step(self):
        if self.running_process is None:
            # Find a process that can safely get its needed resources
            for i, p in enumerate(self.ready_queue):
                if (np.all(p.needed_resources <= self.resource_manager.available_resources) 
                    and self.is_safe(p)):
                    self.running_process = self.ready_queue[i]
                    del self.ready_queue[i]
                    
                    # Allocate resources
                    self.resource_manager.available_resources -= self.running_process.needed_resources
                    self.running_process.allocated_resources += self.running_process.needed_resources
                    self.running_process.needed_resources = np.zeros_like(self.running_process.needed_resources)
                    break
                    
        if self.running_process:
            # Execute the process
            self.running_process.remaining_time -= 1
            self.running_process.execution_time += 1
            
            # Update waiting times
            self.update_waiting_times()
            
            # Record history
            self.history.append({
                'time': self.time,
                'running': self.running_process.pid,
                'ready_queue': [p.pid for p in self.ready_queue],
                'completed': [p.pid for p in self.completed_processes],
                'available': self.resource_manager.available_resources.copy()
            })
            
            # Check completion
            if self.running_process.remaining_time <= 0:
                # Release resources
                self.resource_manager.available_resources += self.running_process.allocated_resources
                self.completed_processes.append(self.running_process)
                self.running_process = None
                
        super().step()

def prepare_processes_for_scheduling(resource_manager, burst_times=None, priorities=None):
    """Prepare processes with proper scheduling attributes"""
    processes = []
    
    # Handle case where resource_manager is actually a list of processes
    if isinstance(resource_manager, list) and all(isinstance(p, Process) for p in resource_manager):
        # Use these processes directly
        process_list = resource_manager
    else:
        # Handle ResourceManager cases
        if isinstance(resource_manager, ResourceManager):
            manager = resource_manager
        elif isinstance(resource_manager, list) and len(resource_manager) > 0 and isinstance(resource_manager[0], ResourceManager):
            manager = resource_manager[0]
        elif hasattr(resource_manager, 'processes'):
            manager = resource_manager
        else:
            raise ValueError("resource_manager must be a ResourceManager, list of Processes, or have a processes attribute")
        
        process_list = manager.processes
    
    burst_times = burst_times or {}
    priorities = priorities or {}
    
    for p in process_list:
        # Create a copy to avoid modifying original
        new_p = Process(p.pid, p.max_resources.copy(), 
                       p.allocated_resources.copy(), 
                       p.needed_resources.copy())
        
        # Set scheduling attributes
        new_p.burst_time = burst_times.get(p.pid, 10)
        new_p.remaining_time = new_p.burst_time
        new_p.priority = priorities.get(p.pid, 1)
        new_p.arrival_time = 0  # Default arrival time
        
        processes.append(new_p)
    return processes


def run_scheduling_simulation(resource_manager, algorithm='fcfs', **kwargs):
    """Run scheduling simulation with specified algorithm"""
    try:
        processes = prepare_processes_for_scheduling(
            resource_manager,
            kwargs.get('burst_times', {}),
            kwargs.get('priorities', {})
        )
        
        if algorithm.lower() == 'fcfs':
            scheduler = FCFSScheduler(processes)
        elif algorithm.lower() == 'rr':
            scheduler = RoundRobinScheduler(processes, kwargs.get('time_quantum', 2))
        elif algorithm.lower() == 'bankers':
            if isinstance(resource_manager, ResourceManager):
                manager = resource_manager
            elif isinstance(resource_manager, list) and isinstance(resource_manager[0], ResourceManager):
                manager = resource_manager[0]
            else:
                manager = resource_manager
            scheduler = BankersScheduler(manager, processes)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        history = scheduler.run_simulation(kwargs.get('max_steps', 1000))
        
        # Attach history to scheduler for backward compatibility
        scheduler.history = history
        
        return scheduler, history
        
    except Exception as e:
        raise ValueError(f"Failed to run simulation: {str(e)}") from e