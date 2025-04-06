# app.py

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import numpy as np
import io
from PIL import Image, ImageTk
import base64
import threading
import time


# Import our modules
from deadlock_core import Process, ResourceManager, create_deadlock_scenario
from scheduling import run_scheduling_simulation
from visualization import (
    create_resource_allocation_graph, 
    plot_resource_allocation_graph, 
    plot_matrices,
    plot_scheduling_gantt
)

class Process:
    def __init__(self, pid, resources):
        self.pid = pid
        self.resources = resources

    def copy(self):
        return Process(self.pid, self.resources.copy())  # Copying resources if it's a list/dict


class DeadlockSimulatorApp:
    """Main application class for the Deadlock Simulator."""
    
    def __init__(self, root):
        """
        Initialize the application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Deadlock Simulator")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Resource manager and other state variables
        self.resource_manager = None
        self.deadlock_processes = []
        self.resolution_type = None
        self.scheduler = None
        self.scheduler_history = []
        
        # Create UI components
        self.create_ui()
        
        # Load initial scenario
        self.load_scenario(1)
    
    def create_ui(self):
        """Create the user interface components."""
        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create top control panel
        self.create_control_panel(main_frame)
        
        # Create tabs for different views
        self.tabs = ttk.Notebook(main_frame)
        self.tabs.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Create tab for deadlock detection
        self.detection_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.detection_tab, text="Deadlock Detection")
        self.create_detection_tab(self.detection_tab)
        
        # Create tab for resource visualization
        self.resource_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.resource_tab, text="Resource Matrices")
        self.create_resource_tab(self.resource_tab)
        
        # Create tab for scheduling
        self.scheduling_tab = ttk.Frame(self.tabs)
        self.tabs.add(self.scheduling_tab, text="Process Scheduling")
        self.create_scheduling_tab(self.scheduling_tab)
        
        # Create status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(5, 0))
    
    def create_control_panel(self, parent):
        """Create the top control panel."""
        control_frame = ttk.LabelFrame(parent, text="Control Panel", padding=(10, 5))
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create scenario selection
        scenario_frame = ttk.Frame(control_frame)
        scenario_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(scenario_frame, text="Deadlock Scenario:").pack(side=tk.LEFT)
        
        self.scenario_var = tk.IntVar(value=1)
        scenario_combo = ttk.Combobox(scenario_frame, textvariable=self.scenario_var, width=5)
        scenario_combo['values'] = tuple(range(1, 10))
        scenario_combo.pack(side=tk.LEFT, padx=(5, 0))
        
        scenario_load_btn = ttk.Button(scenario_frame, text="Load", command=self.on_load_scenario)
        scenario_load_btn.pack(side=tk.LEFT, padx=(5, 10))
        
        # Create deadlock detection button
        detect_btn = ttk.Button(control_frame, text="Detect Deadlock", command=self.on_detect_deadlock)
        detect_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Create resolution buttons
        resolution_frame = ttk.Frame(control_frame)
        resolution_frame.pack(side=tk.LEFT)
        
        ttk.Label(resolution_frame, text="Resolution:").pack(side=tk.LEFT)
        
        term_btn = ttk.Button(resolution_frame, text="Terminate Processes", 
                              command=self.on_resolve_by_termination)
        term_btn.pack(side=tk.LEFT, padx=(5, 5))
        
        preempt_btn = ttk.Button(resolution_frame, text="Resource Preemption", 
                                 command=self.on_resolve_by_preemption)
        preempt_btn.pack(side=tk.LEFT)
        
        # Create reset button
        reset_btn = ttk.Button(control_frame, text="Reset", command=self.on_reset)
        reset_btn.pack(side=tk.RIGHT, padx=(10, 0))
    
    def create_detection_tab(self, parent):
        """Create the deadlock detection tab."""
        # Split into left and right panes
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left pane: Graph visualization
        graph_frame = ttk.LabelFrame(paned, text="Resource Allocation Graph", padding=(5, 5))
        paned.add(graph_frame, weight=70)
        
        self.graph_canvas = tk.Canvas(graph_frame, bg="white")
        self.graph_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Right pane: Process and resource information
        info_frame = ttk.LabelFrame(paned, text="System State", padding=(5, 5))
        paned.add(info_frame, weight=30)
        
        # Create text widget for process information
        self.process_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, height=15)
        self.process_text.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        # Create deadlock status text
        self.deadlock_text = scrolledtext.ScrolledText(info_frame, wrap=tk.WORD, height=8)
        self.deadlock_text.pack(fill=tk.BOTH, expand=True)
    
    def create_resource_tab(self, parent):
        """Create the resource matrices tab."""
        # Frame for matrix visualization
        matrix_frame = ttk.Frame(parent, padding=(5, 5))
        matrix_frame.pack(fill=tk.BOTH, expand=True)
        
        self.matrix_canvas = tk.Canvas(matrix_frame, bg="white")
        self.matrix_canvas.pack(fill=tk.BOTH, expand=True)
    
    def create_scheduling_tab(self, parent):
        """Create the process scheduling tab."""
        # Top frame for scheduling controls
        control_frame = ttk.Frame(parent, padding=(5, 5))
        control_frame.pack(fill=tk.X)
        
        # Scheduling algorithm selection
        ttk.Label(control_frame, text="Scheduling Algorithm:").pack(side=tk.LEFT)
        
        self.algorithm_var = tk.StringVar(value="fcfs")
        algorithm_combo = ttk.Combobox(control_frame, textvariable=self.algorithm_var, width=15)
        algorithm_combo['values'] = ("FCFS", "SJF", "Priority", "Round Robin", "Bankers")
        algorithm_combo.pack(side=tk.LEFT, padx=(5, 10))
        
        # Time quantum for Round Robin
        ttk.Label(control_frame, text="Time Quantum:").pack(side=tk.LEFT)
        
        self.quantum_var = tk.IntVar(value=2)
        quantum_spin = ttk.Spinbox(control_frame, from_=1, to=10, textvariable=self.quantum_var, width=5)
        quantum_spin.pack(side=tk.LEFT, padx=(5, 10))
        
        # Run button
        run_btn = ttk.Button(control_frame, text="Run Simulation", command=self.on_run_scheduling)
        run_btn.pack(side=tk.LEFT)
        
        # Frame for scheduling visualization
        viz_frame = ttk.LabelFrame(parent, text="Scheduling Visualization", padding=(5, 5))
        viz_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.scheduling_canvas = tk.Canvas(viz_frame, bg="white")
        self.scheduling_canvas.pack(fill=tk.BOTH, expand=True)
    
    def load_scenario(self, scenario_id):
        """
        Load a deadlock scenario.
        
        Args:
            scenario_id: ID of the scenario to load
        """
        # Reset state
        self.deadlock_processes = []
        self.resolution_type = None
        
        # Create resource manager with the scenario
        self.resource_manager = create_deadlock_scenario(scenario_id)
        
        # Update UI
        self.update_process_info()
        self.update_deadlock_info()
        self.update_graph_visualization()
        self.update_matrix_visualization()
        
        self.status_var.set(f"Loaded deadlock scenario {scenario_id}")
    
    def update_process_info(self):
        """Update the process information text."""
        if not self.resource_manager:
            return
            
        self.process_text.delete(1.0, tk.END)
        self.process_text.insert(tk.END, "PROCESSES:\n")
        
        for p in self.resource_manager.processes:
            self.process_text.insert(tk.END, f"Process {p.pid}:\n")
            self.process_text.insert(tk.END, f"  Max: {p.max_resources}\n")
            self.process_text.insert(tk.END, f"  Allocated: {p.allocated_resources}\n")
            self.process_text.insert(tk.END, f"  Need: {p.needed_resources}\n\n")
        
        self.process_text.insert(tk.END, "RESOURCES:\n")
        self.process_text.insert(tk.END, f"Available: {self.resource_manager.available_resources}\n")
    
    def update_deadlock_info(self):
        """Update the deadlock status text."""
        self.deadlock_text.delete(1.0, tk.END)
        
        if self.deadlock_processes:
            self.deadlock_text.insert(tk.END, "DEADLOCK DETECTED!\n")
            self.deadlock_text.insert(tk.END, "Deadlocked Processes:\n")
            
            for p in self.deadlock_processes:
                self.deadlock_text.insert(tk.END, f"  Process {p.pid}\n")
                
            if self.resolution_type:
                self.deadlock_text.insert(tk.END, f"\nDeadlock resolved by: {self.resolution_type}\n")
        else:
            if self.resolution_type:
                self.deadlock_text.insert(tk.END, f"Deadlock resolved by: {self.resolution_type}\n")
            else:
                self.deadlock_text.insert(tk.END, "No deadlock detected in the current state.\n")
    
    def update_graph_visualization(self):
        """Update the resource allocation graph visualization."""
        if not self.resource_manager:
            return
            
        # Create graph
        G = create_resource_allocation_graph(self.resource_manager)
        
        # Generate plot
        img_str = plot_resource_allocation_graph(
            G, 
            self.deadlock_processes if self.deadlock_processes else None,
            None,
            self.resolution_type
        )
        
        # Display image
        self.display_image(self.graph_canvas, img_str)
    
    def update_matrix_visualization(self):
        """Update the resource matrices visualization."""
        if not self.resource_manager:
            return
            
        # Generate plot
        img_str = plot_matrices(self.resource_manager)
        
        # Display image
        self.display_image(self.matrix_canvas, img_str)
    
    def update_scheduling_visualization(self):
        """Update the scheduling visualization."""
        if not self.scheduler:
            return
            
        # Generate plot
        img_str = plot_scheduling_gantt(self.scheduler)
        
        if img_str:
            # Display image
            self.display_image(self.scheduling_canvas, img_str)
    
    def display_image(self, canvas, img_str):
        """
        Display a base64 encoded image on a canvas.
        
        Args:
            canvas: Tkinter Canvas
            img_str: Base64 encoded image
        """
        # Clear canvas
        canvas.delete("all")
        
        if not img_str:
            return
            
        # Decode image
        img_data = base64.b64decode(img_str)
        img = Image.open(io.BytesIO(img_data))
        
        # Resize to fit canvas
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:
            # Calculate scaling to maintain aspect ratio
            img_width, img_height = img.size
            scale = min(canvas_width / img_width, canvas_height / img_height)
            
            new_width = int(img_width * scale)
            new_height = int(img_height * scale)
            
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        # Display image
        photo = ImageTk.PhotoImage(img)
        canvas.create_image(canvas.winfo_width() // 2, canvas.winfo_height() // 2, 
                           image=photo, anchor=tk.CENTER)
        
        # Keep a reference to prevent garbage collection
        canvas.image = photo
    
    def on_load_scenario(self):
        """Handle scenario load button click."""
        scenario_id = self.scenario_var.get()
        self.load_scenario(scenario_id)
    
    def on_detect_deadlock(self):
        """Handle deadlock detection button click."""
        if not self.resource_manager:
            return
            
        # Detect deadlock
        self.deadlock_processes = self.resource_manager.detect_deadlock()
        
        # Reset resolution type
        self.resolution_type = None
        
        # Update UI
        self.update_deadlock_info()
        self.update_graph_visualization()
        
        if self.deadlock_processes:
            self.status_var.set(f"Deadlock detected! {len(self.deadlock_processes)} processes are deadlocked.")
        else:
            self.status_var.set("No deadlock detected in the current state.")
    
    def on_resolve_by_termination(self):
        """Handle termination resolution button click."""
        if not self.resource_manager or not self.deadlock_processes:
            messagebox.showinfo("No Deadlock", "No deadlock detected to resolve.")
            return
            
        # Resolve deadlock by termination
        terminated = self.resource_manager.resolve_deadlock_by_termination()
        
        # Update state
        self.deadlock_processes = []
        self.resolution_type = "Process Termination"
        
        # Update UI
        self.update_process_info()
        self.update_deadlock_info()
        self.update_graph_visualization()
        self.update_matrix_visualization()
        
        self.status_var.set(f"Deadlock resolved by terminating {len(terminated)} processes.")
    
    def on_resolve_by_preemption(self):
        """Handle preemption resolution button click."""
        if not self.resource_manager or not self.deadlock_processes:
            messagebox.showinfo("No Deadlock", "No deadlock detected to resolve.")
            return

        # Resolve deadlock by preemption
        preempted = self.resource_manager.resolve_deadlock_by_preemption()

        # Update state
        self.deadlock_processes = []
        self.resolution_type = "Resource Preemption"

        # Update UI
        self.update_process_info()
        self.update_deadlock_info()
        self.update_graph_visualization()
        self.update_matrix_visualization()

        self.status_var.set(f"Deadlock resolved by preempting resources from {len(preempted)} processes.")
    

    def on_reset(self):
        """Handle reset button click."""
        scenario_id = self.scenario_var.get()
        self.load_scenario(scenario_id)
        self.status_var.set(f"Reset to initial state of scenario {scenario_id}.")


    def on_run_scheduling(self):
        """Handle run scheduling button click."""
        if not self.resource_manager:
            return

        # Get scheduling parameters
        algorithm = self.algorithm_var.get().lower()
        time_quantum = self.quantum_var.get()

        # Run scheduling simulation in a separate thread to avoid UI freezing
        def run_simulation():
            # Create a copy of processes to avoid modifying the original
            # processes = [p.copy() for p in self.resource_manager.processes]
            import copy
            processes = [copy.deepcopy(p) for p in self.resource_manager.processes]


            # Run simulation
            self.scheduler = run_scheduling_simulation(processes, algorithm, time_quantum=None)

            # Update UI in the main thread
            self.root.after(0, self.update_scheduling_visualization)
            self.root.after(0, lambda: self.status_var.set(f"Scheduling simulation completed using {algorithm.upper()}."))

        # Show loading message
        self.status_var.set(f"Running {algorithm.upper()} scheduling simulation...")

        # Start simulation thread
        threading.Thread(target=run_simulation, daemon=True).start()

        # Switch to scheduling tab
        self.tabs.select(self.scheduling_tab)


# Helper methods for animations and custom scenarios could be added here
def animate_execution(self, execution_steps):
    """Animate the execution of processes."""
    for step in execution_steps:
        # Update UI based on step
        self.update_process_info()
        self.update_graph_visualization()
        self.root.update()
        time.sleep(0.5)  # Delay between steps

def create_custom_scenario(self):
    """Open a dialog to create a custom scenario."""
    # Implementation would create a new window with inputs for processes and resources
    dialog = tk.Toplevel(self.root)
    dialog.title("Create Custom Scenario")
    dialog.geometry("600x500")
    
    # Add controls for defining processes, resources, and their relationships
    # ...
    
    # Button to create and load the custom scenario
    def create_and_load():
        # Get values from inputs and create resource manager
        # ...
        dialog.destroy()
    
    create_btn = ttk.Button(dialog, text="Create Scenario", command=create_and_load)
    create_btn.pack(pady=10)


# Main application entry point
def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = DeadlockSimulatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()


