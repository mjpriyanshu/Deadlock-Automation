🧠 Deadlock Detection and Resolution Tool
A Python-based desktop application to detect, simulate, and resolve deadlocks in real time, built with GUI and visualization support. This tool is perfect for demonstrating and understanding deadlock scenarios in Operating Systems.

🔧 Features
🕵️ Real-Time Deadlock Detection
Monitors system processes and resource allocations to detect deadlocks on the fly.

🎮 Simulation Mode
If no deadlocks are detected, users can simulate predefined deadlock scenarios to see how deadlocks occur and how they are resolved.

📊 Resource Allocation Matrix
Displays a dynamic matrix showing current allocation and request states of processes and resources.

🌐 Visual Graph Representation
Uses NetworkX and Matplotlib to visualize:

Resource Allocation Graph (RAG)

Deadlock cycles

Resolutions via pre-defined strategies

🖥️ User-Friendly Interface
Built using Tkinter for intuitive interaction and control.

🛠️ Tech Stack

Tool / Library	Purpose
Python	Core programming language
Tkinter	GUI development
NetworkX	Deadlock graph construction and cycle detection
Matplotlib	Visual representation of graphs
NumPy	Matrix operations


🚀 Getting Started
Prerequisites
Make sure you have Python 3.x installed along with the following packages:

bash:
pip install tkinter matplotlib networkx numpy

Run the Tool in bash:
python app.py

🧪 Usage
Launch the app to monitor live resource allocations.

If deadlock is detected, the tool shows:

The cycle in the graph

Involved processes and resources

Suggested resolution

If no deadlock, click on "Simulate Deadlock" to:

Select a predefined scenario

Visualize its graph

View how it's resolved step-by-step

📂 Project Structure

.
├── app.py                   # Initializes GUI and manages user interaction

├── main.py                  # Entry point for launching the app

├── deadlock_core.py         # Core logic for deadlock detection

├── deadlock_resolution.py   # Strategies and steps for resolving deadlocks

├── realtimeDetection.py     # Monitors and detects deadlocks in real time

├── scheduling.py            # Simulates process scheduling behavior

├── test.py                  # Test cases and debugging utilities

├── visualization.py         # Handles graph drawing and visualization

└── README.md


🧪 How to Use
Start the app: Automatically checks for current resource allocations.

If deadlock is detected:

Shows a graph with the cycle

Displays involved processes/resources

Suggests or shows a resolution path

If no deadlock, click "Simulate Deadlock":

Choose a predefined scenario

Visualize the deadlock and its resolution

See the resource allocation matrix update in real time



📌 Concepts Implemented
Resource Allocation Graphs (RAG)

Deadlock Cycle Detection

Process Scheduling

Resource Allocation Matrix

Deadlock Resolution Strategies

🔮 Future Enhancements
Allow users to define custom deadlock scenarios

Export visualizations and logs

Add support for distributed system deadlock detection

Improve resolution algorithms
