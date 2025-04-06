# main.py

import tkinter as tk
from deadlock_core import SystemState, Process, Resource, DeadlockDetector
from scheduling import Scheduler
from deadlock_resolution import DeadlockResolver
from visualization import DeadlockVisualizer
from app import DeadlockSimulationUI

def create_deadlock_scenario(system_state, scenario_id):
    """
    Create a predefined deadlock scenario
    
    Args:
        system_state: The SystemState object to modify
        scenario_id: Integer ID of the scenario to create
    """
    # Clear current state
    system_state.clear()
    
    if scenario_id == 1:
        # Scenario 1: Simple circular wait deadlock
        # Create 3 processes and 3 resources
        p0 = Process(0, "Process 0", priority=1)
        p1 = Process(1, "Process 1", priority=2)
        p2 = Process(2, "Process 2", priority=3)
        
        r0 = Resource(0, "Resource 0", instances=1)
        r1 = Resource(1, "Resource 1", instances=1)
        r2 = Resource(2, "Resource 2", instances=1)
        
        # Add processes and resources to the system
        system_state.add_process(p0)
        system_state.add_process(p1)
        system_state.add_process(p2)
        
        system_state.add_resource(r0)
        system_state.add_resource(r1)
        system_state.add_resource(r2)
        
        # Set up allocation (resources currently held by processes)
        system_state.allocate_resource(p0.id, r0.id, 1)
        system_state.allocate_resource(p1.id, r1.id, 1)
        system_state.allocate_resource(p2.id, r2.id, 1)
        
        # Set up resource requests (resources needed by processes)
        system_state.request_resource(p0.id, r1.id, 1)
        system_state.request_resource(p1.id, r2.id, 1)
        system_state.request_resource(p2.id, r0.id, 1)
        
    elif scenario_id == 2:
        # Scenario 2: Multiple instance deadlock
        # Create 4 processes and 2 resources with multiple instances
        p0 = Process(0, "Process 0", priority=3)
        p1 = Process(1, "Process 1", priority=1)
        p2 = Process(2, "Process 2", priority=4)
        p3 = Process(3, "Process 3", priority=2)
        
        r0 = Resource(0, "Resource A", instances=3)
        r1 = Resource(1, "Resource B", instances=2)
        
        # Add processes and resources to the system
        system_state.add_process(p0)
        system_state.add_process(p1)
        system_state.add_process(p2)
        system_state.add_process(p3)
        
        system_state.add_resource(r0)
        system_state.add_resource(r1)
        
        # Set up allocation
        system_state.allocate_resource(p0.id, r0.id, 1)
        system_state.allocate_resource(p0.id, r1.id, 1)
        system_state.allocate_resource(p1.id, r0.id, 1)
        system_state.allocate_resource(p2.id, r0.id, 1)
        system_state.allocate_resource(p2.id, r1.id, 1)
        
        # Set up resource requests
        system_state.request_resource(p0.id, r0.id, 1)  # P0 needs 1 more of R0
        system_state.request_resource(p1.id, r1.id, 1)  # P1 needs 1 of R1
        system_state.request_resource(p3.id, r0.id, 1)  # P3 needs 1 of R0
        system_state.request_resource(p3.id, r1.id, 1)  # P3 needs 1 of R1
        
    elif scenario_id == 3:
        # Scenario 3: Deadlock with different process priorities
        p0 = Process(0, "High Priority", priority=10)
        p1 = Process(1, "Medium Priority", priority=5)
        p2 = Process(2, "Low Priority", priority=1)
        
        r0 = Resource(0, "Resource X", instances=1)
        r1 = Resource(1, "Resource Y", instances=1)
        r2 = Resource(2, "Resource Z", instances=1)
        
        system_state.add_process(p0)
        system_state.add_process(p1)
        system_state.add_process(p2)
        
        system_state.add_resource(r0)
        system_state.add_resource(r1)
        system_state.add_resource(r2)
        
        # Set up deadlock where higher priority processes hold resources
        # needed by lower priority processes and vice versa
        system_state.allocate_resource(p0.id, r0.id, 1)
        system_state.allocate_resource(p1.id, r1.id, 1)
        system_state.allocate_resource(p2.id, r2.id, 1)
        
        system_state.request_resource(p0.id, r1.id, 1)
        system_state.request_resource(p1.id, r2.id, 1)
        system_state.request_resource(p2.id, r0.id, 1)
        
    elif scenario_id == 4:
        # Scenario 4: No deadlock - safe state
        p0 = Process(0, "Process A", priority=2)
        p1 = Process(1, "Process B", priority=1)
        
        r0 = Resource(0, "CPU", instances=3)
        r1 = Resource(1, "Memory", instances=4)
        
        system_state.add_process(p0)
        system_state.add_process(p1)
        
        system_state.add_resource(r0)
        system_state.add_resource(r1)
        
        # Safe allocation that won't cause deadlock
        system_state.allocate_resource(p0.id, r0.id, 1)
        system_state.allocate_resource(p1.id, r1.id, 2)
        
        system_state.request_resource(p0.id, r1.id, 1)
        system_state.request_resource(p1.id, r0.id, 1)
        
    else:
        # Default scenario if no match
        print(f"Scenario {scenario_id} not defined, creating default scenario")
        
        # Create a simple default scenario
        p0 = Process(0, "Default P0", priority=1)
        r0 = Resource(0, "Default R0", instances=1)
        
        system_state.add_process(p0)
        system_state.add_resource(r0)

def main():
    # Create the main application window
    root = tk.Tk()
    root.title("Deadlock Simulation Tool")
    root.geometry("1200x800")
    
    # Create the system state
    system_state = SystemState()
    
    # Create detector, resolver, visualizer and scheduler
    detector = DeadlockDetector(system_state)
    resolver = DeadlockResolver(system_state)
    visualizer = DeadlockVisualizer(system_state)
    scheduler = Scheduler(system_state)
    
    # Create the UI and pass all components
    app = DeadlockSimulationUI(
        root, 
        system_state, 
        detector, 
        resolver, 
        visualizer, 
        scheduler
    )
    
    # Add a method to load scenarios
    def load_scenario(scenario_id):
        create_deadlock_scenario(system_state, scenario_id)
        app.update_display()  # Update the UI to reflect the new state
    
    # Add scenario selection to UI (this relies on your UI class having a control_panel attribute)
    scenario_frame = tk.Frame(app.control_panel)
    scenario_frame.pack(fill=tk.X, padx=10, pady=5)
    
    tk.Label(scenario_frame, text="Load Scenario:").pack(side=tk.LEFT)
    
    for i in range(1, 5):  # For scenarios 1-4
        scenario_button = tk.Button(
            scenario_frame, 
            text=f"Scenario {i}", 
            command=lambda id=i: load_scenario(id)
        )
        scenario_button.pack(side=tk.LEFT, padx=5)
    
    # Start the application
    root.mainloop()

if __name__ == "__main__":
    main()