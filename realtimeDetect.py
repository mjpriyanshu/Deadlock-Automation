import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import threading, time
import networkx as nx
from tkinter import ttk

# Global dictionaries to track each lock’s owner and threads’ waiting lists
lock_owner = {}      # Maps MonitorLock id to owning thread name
waiting_info = {}    # Maps thread name to list of MonitorLock instances it's waiting for

class MonitorLock:
    def __init__(self):
        self._lock = threading.Lock()
        self._owner = None

    def acquire(self, blocking=True, timeout=-1):
        current = threading.current_thread().name
        waiting_info.setdefault(current, []).append(self)
        acquired = self._lock.acquire(blocking, timeout)
        if acquired:
            self._owner = current
            waiting_info[current].remove(self)
        return acquired

    def release(self):
        self._owner = None
        self._lock.release()

    @property
    def owner(self):
        return self._owner

def detect_deadlock():
    # Build a wait-for graph: For each thread waiting on a lock that is held,
    # add an edge from the waiting thread to the current lock owner.
    graph = nx.DiGraph()
    for thread, locks in waiting_info.items():
        for lock in locks:
            owner = lock.owner
            if owner and owner != thread:
                graph.add_edge(thread, owner)
    try:
        cycle = nx.find_cycle(graph, orientation='original')
        return cycle
    except nx.exception.NetworkXNoCycle:
        return None

def thread_job(lock1, lock2, log_func):
    current = threading.current_thread().name
    log_func(f"{current}: Attempting to acquire {lock1}")
    lock1.acquire()
    log_func(f"{current}: Acquired Lock1")
    time.sleep(1)
    log_func(f"{current}: Attempting to acquire {lock2}")
    lock2.acquire()
    log_func(f"{current}: Acquired Lock2")
    time.sleep(1)
    lock2.release()
    log_func(f"{current}: Released Lock2")
    lock1.release()
    log_func(f"{current}: Released Lock1")

class DeadlockDetectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-Time Deadlock & Scheduling Tool")
        self.root.geometry("750x600")  # increased size
        
        # NEW: Setup menu bar for a professional look
        menubar = tk.Menu(root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Exit", command=root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        root.config(menu=menubar)
        
        # Setup ttk style for modern look
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TLabel", font=("Segoe UI", 14), background="#f0f0f0")
        style.configure("TButton", font=("Segoe UI", 12), padding=6)
        style.configure("Header.TLabel", font=("Segoe UI", 22, "bold"), foreground="#333333", background="#f0f0f0")
        
        # Header Frame
        header_frame = ttk.Frame(root)
        header_frame.pack(pady=10)
        ttk.Label(header_frame, text="Real-Time Deadlock & Scheduling Tool", style="Header.TLabel").pack()
        
        # Activity log
        self.log_box = scrolledtext.ScrolledText(root, width=80, height=15, font=("Segoe UI", 10))
        self.log_box.pack(pady=10)
        
        # Control Panel Frame with grid layout for professional appearance
        control_frame = ttk.Frame(root, padding=(20, 10))
        control_frame.pack(pady=10, fill="x")
        
        # Deadlock Check Button
        ttk.Button(control_frame, text="Check Deadlock", command=self.check_deadlock).grid(row=0, column=0, padx=10, pady=8, sticky="ew")
        
        # Scheduling algorithm drop-down
        ttk.Label(control_frame, text="Scheduling Algorithm:").grid(row=1, column=0, padx=10, pady=(12, 4), sticky="w")
        self.sched_algo = tk.StringVar(value="Round Robin")
        options = ["FCFS", "Round Robin", "Shortest Job First", "Priority"]
        option_menu = ttk.OptionMenu(control_frame, self.sched_algo, self.sched_algo.get(), *options)
        option_menu.grid(row=1, column=1, padx=10, pady=(12, 4), sticky="ew")
        
        # Start Process Scheduling Button (runs scheduler and shows Gantt chart)
        ttk.Button(control_frame, text="Start Process Scheduling", command=self.start_process_scheduling)\
            .grid(row=2, column=0, columnspan=2, padx=10, pady=8, sticky="ew")
        
        # Configure grid weights for equal column distribution
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        
        # Background monitoring thread and scheduling events storage remain unchanged
        self.monitoring = True
        threading.Thread(target=self.monitor_loop, daemon=True).start()
        self.gantt_data = []
    
    def log(self, message):
        # Make UI updates thread-safe using root.after
        self.root.after(0, lambda: self.log_box.insert(tk.END, message + "\n"))
        self.root.after(0, lambda: self.log_box.see(tk.END))
    
    def check_deadlock(self):
        cycle = detect_deadlock()
        if cycle:
            self.log(f"Deadlock Detected: {cycle}")
            messagebox.showwarning("Deadlock Detected", f"Cycle: {cycle}")
        else:
            self.log("No deadlock detected.")
            messagebox.showinfo("No Deadlock", "No deadlock detected.")
    
    def monitor_loop(self):
        while self.monitoring:
            cycle = detect_deadlock()
            if cycle:
                self.log(f"Monitor: Deadlock detected: {cycle}")
            time.sleep(2)
    
    # Process scheduling simulation for multiple algorithms
    def run_scheduler(self):
        # Define sample processes with burst time and priority
        processes = [
            {'pid': 'P1', 'burst': 5, 'remaining': 5, 'priority': 2},
            {'pid': 'P2', 'burst': 3, 'remaining': 3, 'priority': 1},
            {'pid': 'P3', 'burst': 7, 'remaining': 7, 'priority': 3},
        ]
        algo = self.sched_algo.get()
        schedule = []  # Each event: (pid, start_time, duration)
        current_time = 0
        
        if algo == "FCFS":
            for proc in processes:
                schedule.append((proc['pid'], current_time, proc['burst']))
                current_time += proc['burst']
        elif algo == "Round Robin":
            time_quantum = 2
            done = False
            while not done:
                done = True
                for proc in processes:
                    if proc['remaining'] > 0:
                        done = False
                        exec_time = min(time_quantum, proc['remaining'])
                        schedule.append((proc['pid'], current_time, exec_time))
                        current_time += exec_time
                        proc['remaining'] -= exec_time
        elif algo == "Shortest Job First":
            sorted_procs = sorted(processes, key=lambda p: p['burst'])
            for proc in sorted_procs:
                schedule.append((proc['pid'], current_time, proc['burst']))
                current_time += proc['burst']
        elif algo == "Priority":
            sorted_procs = sorted(processes, key=lambda p: p['priority'])
            for proc in sorted_procs:
                schedule.append((proc['pid'], current_time, proc['burst']))
                current_time += proc['burst']
        else:
            self.log("Unknown Scheduling Algorithm selected.")
            return
        
        self.gantt_data = schedule
        self.log(f"Scheduler executed using {algo} algorithm. Gantt data:")
        for event in schedule:
            self.log(f"Process {event[0]}: start {event[1]}, duration {event[2]}")
    
    # Display Gantt Chart using matplotlib
    def show_gantt(self):
        if not self.gantt_data:
            self.log("No Gantt data available. Run scheduler first.")
            messagebox.showinfo("Gantt Chart", "No schedule data available. Please run scheduler first.")
            return
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 4))
        yticks = []
        yticklabels = []
        colors = {'P1': 'tab:blue', 'P2': 'tab:orange', 'P3': 'tab:green'}
        for event in self.gantt_data:
            pid, start, duration = event
            if pid not in yticks:
                yticks.append(pid)
                yticklabels.append(pid)
            ax.broken_barh([(start, duration)], (yticks.index(pid)*10, 9), facecolors=colors.get(pid, 'gray'))
        ax.set_xlabel("Time")
        ax.set_ylabel("Process")
        ax.set_yticks([i*10+4.5 for i in range(len(yticks))])
        ax.set_yticklabels(yticklabels)
        ax.set_title("Gantt Chart - Process Scheduling")
        plt.tight_layout()
        plt.show()
    
    # Run scheduler and immediately show Gantt chart
    def start_process_scheduling(self):
        self.run_scheduler()
        self.show_gantt()

if __name__ == "__main__":
    root = tk.Tk()
    app = DeadlockDetectorGUI(root)
    root.mainloop()
