# deadlock_resolution.py

class DeadlockResolver:
    def __init__(self, system_state):
        """
        Initialize the deadlock resolver with the current system state.
        
        Args:
            system_state: A SystemState object containing processes, resources, and allocation information
        """
        self.system_state = system_state
    
    def resource_preemption(self, deadlock_processes):
        """
        Resolves deadlock by preempting resources from processes.
        Chooses the process with the minimum cost of preemption.
        
        Args:
            deadlock_processes: List of processes in deadlock
        
        Returns:
            A dict with resolution details including affected processes and resources
        """
        resolution_steps = []
        remaining_deadlocked = deadlock_processes.copy()
        
        while remaining_deadlocked:
            # Find the process with minimum resources to preempt
            min_cost = float('inf')
            victim_process = None
            
            for process in remaining_deadlocked:
                # Calculate preemption cost (could be based on priority, resources held, etc.)
                cost = sum(self.system_state.allocation_matrix[process.id])
                if cost < min_cost:
                    min_cost = cost
                    victim_process = process
            
            if victim_process:
                # Preempt all resources from the victim process
                preempted_resources = []
                for i, count in enumerate(self.system_state.allocation_matrix[victim_process.id]):
                    if count > 0:
                        self.system_state.available_resources[i] += count
                        self.system_state.allocation_matrix[victim_process.id][i] = 0
                        preempted_resources.append((i, count))
                
                resolution_steps.append({
                    'action': 'preempt',
                    'process': victim_process.id,
                    'resources': preempted_resources
                })
                
                # Remove the process from deadlocked list
                remaining_deadlocked.remove(victim_process)
                
                # Update process state
                victim_process.state = 'terminated'
            
        return {
            'type': 'resource_preemption',
            'steps': resolution_steps
        }
    
    def process_termination(self, deadlock_processes):
        """
        Resolves deadlock by terminating processes one by one until deadlock is broken.
        
        Args:
            deadlock_processes: List of processes in deadlock
        
        Returns:
            A dict with resolution details including terminated processes
        """
        resolution_steps = []
        remaining_deadlocked = deadlock_processes.copy()
        
        # Sort processes by priority or other criteria to choose termination order
        # Here we'll simply terminate processes in order of increasing priority
        sorted_processes = sorted(remaining_deadlocked, key=lambda p: p.priority)
        
        for process in sorted_processes:
            # Release all resources held by the process
            released_resources = []
            for i, count in enumerate(self.system_state.allocation_matrix[process.id]):
                if count > 0:
                    self.system_state.available_resources[i] += count
                    self.system_state.allocation_matrix[process.id][i] = 0
                    released_resources.append((i, count))
            
            # Update process state
            process.state = 'terminated'
            
            resolution_steps.append({
                'action': 'terminate',
                'process': process.id,
                'released_resources': released_resources
            })
            
            # Check if deadlock is resolved after this termination
            # This would require checking if the remaining processes can complete
            remaining_deadlocked.remove(process)
            if self._check_deadlock_resolved(remaining_deadlocked):
                break
        
        return {
            'type': 'process_termination',
            'steps': resolution_steps
        }
    
    def _check_deadlock_resolved(self, remaining_processes):
        """
        Check if the deadlock is resolved for the remaining processes.
        
        Args:
            remaining_processes: List of processes still in the system
        
        Returns:
            True if deadlock is resolved, False otherwise
        """
        # Create a temporary copy of the system state
        temp_available = self.system_state.available_resources.copy()
        temp_allocation = [self.system_state.allocation_matrix[p.id].copy() for p in remaining_processes]
        temp_request = [self.system_state.request_matrix[p.id].copy() for p in remaining_processes]
        
        # Run a simplified banker's algorithm to check if deadlock is resolved
        work = temp_available.copy()
        finish = [False] * len(remaining_processes)
        
        while True:
            found = False
            for i, process in enumerate(remaining_processes):
                if not finish[i]:
                    # Check if process can complete
                    can_complete = True
                    for j in range(len(temp_request[i])):
                        if temp_request[i][j] > work[j]:
                            can_complete = False
                            break
                    
                    if can_complete:
                        finish[i] = True
                        found = True
                        for j in range(len(work)):
                            work[j] += temp_allocation[i][j]
            
            if not found:
                break
        
        # If all processes are finished, deadlock is resolved
        return all(finish)
    
    def banker_resolution(self, deadlock_processes):
        """
        Apply banker's algorithm principles to resolve deadlock by 
        finding a safe sequence of resource allocation.
        
        Args:
            deadlock_processes: List of processes in deadlock
        
        Returns:
            A dict with resolution details and a safe sequence if found
        """
        resolution_steps = []
        
        # Check if the system can be brought to a safe state
        # First, calculate the total resources needed
        total_resources = self.system_state.available_resources.copy()
        for process in self.system_state.processes:
            for i in range(len(total_resources)):
                total_resources[i] += self.system_state.allocation_matrix[process.id][i]
        
        # Reset the simulation to a new state
        # This is a simplified approach - in real implementation you might want
        # to try different resource distribution strategies
        self.system_state.available_resources = total_resources.copy()
        for process in self.system_state.processes:
            for i in range(len(total_resources)):
                self.system_state.allocation_matrix[process.id][i] = 0
        
        # Now try to find a safe sequence using banker's algorithm
        work = self.system_state.available_resources.copy()
        finish = [False] * len(self.system_state.processes)
        safe_sequence = []
        
        while True:
            found = False
            for i, process in enumerate(self.system_state.processes):
                if not finish[i]:
                    # Check if process's max resources can be satisfied
                    need = [self.system_state.max_matrix[i][j] - self.system_state.allocation_matrix[i][j] 
                            for j in range(len(work))]
                    
                    can_complete = True
                    for j in range(len(need)):
                        if need[j] > work[j]:
                            can_complete = False
                            break
                    
                    if can_complete:
                        finish[i] = True
                        safe_sequence.append(process.id)
                        found = True
                        
                        # Simulate process completion
                        for j in range(len(work)):
                            work[j] += self.system_state.allocation_matrix[i][j]
                        
                        resolution_steps.append({
                            'action': 'allocate_and_complete',
                            'process': process.id,
                            'resources_needed': need,
                            'resources_released': [self.system_state.allocation_matrix[i][j] for j in range(len(work))]
                        })
            
            if not found:
                break
        
        # Check if all processes are in the safe sequence
        if all(finish):
            return {
                'type': 'banker_resolution',
                'success': True,
                'safe_sequence': safe_sequence,
                'steps': resolution_steps
            }
        else:
            # If banker's algorithm couldn't find a solution, return failure
            return {
                'type': 'banker_resolution',
                'success': False
            }
    
    def resolve_deadlock(self, strategy, deadlock_processes):
        """
        Resolve deadlock using the specified strategy.
        
        Args:
            strategy: A string specifying the resolution strategy
                     ('resource_preemption', 'process_termination', or 'banker')
            deadlock_processes: List of processes in deadlock
        
        Returns:
            A dict containing resolution details
        """
        if strategy == 'resource_preemption':
            return self.resource_preemption(deadlock_processes)
        elif strategy == 'process_termination':
            return self.process_termination(deadlock_processes)
        elif strategy == 'banker':
            return self.banker_resolution(deadlock_processes)
        else:
            raise ValueError(f"Unknown deadlock resolution strategy: {strategy}")