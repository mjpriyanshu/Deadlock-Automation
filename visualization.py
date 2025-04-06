# visualization.py

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
import io
import base64



def create_resource_allocation_graph(resource_manager):
    """
    Create a directed graph representing resource allocation.
    
    Args:
        resource_manager: ResourceManager instance
        
    Returns:
        nx.DiGraph: Directed graph of resource allocations
    """
    G = nx.DiGraph()
    
    # Add process nodes
    for p in resource_manager.processes:
        G.add_node(f"P{p.pid}", type="process")
        
    # Add resource nodes
    for i in range(len(resource_manager.available_resources)):
        G.add_node(f"R{i+1}", type="resource")
        
    # Add allocation edges (resource → process)
    for p in resource_manager.processes:
        for i, count in enumerate(p.allocated_resources):
            if count > 0:
                G.add_edge(f"R{i+1}", f"P{p.pid}", type="allocation", weight=count)
                
    # Add request edges (process → resource)
    for p in resource_manager.processes:
        for i, count in enumerate(p.needed_resources):
            if count > 0:
                G.add_edge(f"P{p.pid}", f"R{i+1}", type="request", weight=count)
                
    return G

def plot_resource_allocation_graph(G, deadlock_processes=None, preempted_resources=None, resolution_type=None):
    """
    Plot resource allocation graph.
    
    Args:
        G: NetworkX DiGraph
        deadlock_processes: List of deadlocked processes
        preempted_resources: Dictionary of preempted resources
        resolution_type: Type of deadlock resolution performed
        
    Returns:
        str: Base64 encoded PNG image
    """
    plt.figure(figsize=(10, 8))
    
    # Set positions using spring layout
    pos = nx.spring_layout(G, seed=42)
    
    # Draw process nodes
    process_nodes = [n for n in G.nodes() if G.nodes[n]['type'] == 'process']
    resource_nodes = [n for n in G.nodes() if G.nodes[n]['type'] == 'resource']
    
    # Highlight deadlocked processes if provided
    if deadlock_processes:
        deadlock_node_names = [f"P{p.pid}" for p in deadlock_processes]
        normal_processes = [n for n in process_nodes if n not in deadlock_node_names]
        
        # Draw normal processes
        nx.draw_networkx_nodes(G, pos, nodelist=normal_processes, node_color='lightblue', 
                               node_size=500, node_shape='o')
        
        # Draw deadlocked processes
        nx.draw_networkx_nodes(G, pos, nodelist=deadlock_node_names, node_color='red', 
                               node_size=500, node_shape='o')
    else:
        # Draw all processes normally
        nx.draw_networkx_nodes(G, pos, nodelist=process_nodes, node_color='lightblue', 
                               node_size=500, node_shape='o')
    
    # Draw resource nodes
    nx.draw_networkx_nodes(G, pos, nodelist=resource_nodes, node_color='lightgreen', 
                           node_size=400, node_shape='s')
    
    # Draw edges with different colors based on type
    allocation_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'allocation']
    request_edges = [(u, v) for u, v, d in G.edges(data=True) if d['type'] == 'request']
    
    # Highlight preempted resources if provided
    preempted_edges = []
    if preempted_resources:
        for pid, resources in preempted_resources.items():
            for i, count in enumerate(resources):
                if count > 0:
                    preempted_edges.append((f"R{i+1}", f"P{pid}"))
        
        # Draw normal allocation edges
        normal_allocation_edges = [e for e in allocation_edges if e not in preempted_edges]
        nx.draw_networkx_edges(G, pos, edgelist=normal_allocation_edges, edge_color='blue', width=2)
        
        # Draw preempted edges
        nx.draw_networkx_edges(G, pos, edgelist=preempted_edges, edge_color='purple', 
                               width=2, style='dashed')
    else:
        # Draw all allocation edges normally
        nx.draw_networkx_edges(G, pos, edgelist=allocation_edges, edge_color='blue', width=2)
    
    # Draw request edges
    nx.draw_networkx_edges(G, pos, edgelist=request_edges, edge_color='red', width=1.5, 
                           arrowstyle='->', arrowsize=15)
    
    # Add labels
    nx.draw_networkx_labels(G, pos, font_weight='bold')
    
    # Add edge labels (weights)
    edge_labels = {(u, v): d['weight'] for u, v, d in G.edges(data=True) if d['weight'] > 1}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    
    # Add title based on resolution
    if deadlock_processes and not resolution_type:
        plt.title("Resource Allocation Graph (Deadlock Detected)", fontsize=14)
    elif resolution_type:
        plt.title(f"Resource Allocation Graph (After {resolution_type} Resolution)", fontsize=14)
    else:
        plt.title("Resource Allocation Graph", fontsize=14)
    
    # Add legend
    plt.plot([], [], 'o', color='lightblue', label='Process')
    if deadlock_processes:
        plt.plot([], [], 'o', color='red', label='Deadlocked Process')
    plt.plot([], [], 's', color='lightgreen', label='Resource')
    plt.plot([], [], '-', color='blue', label='Allocation')
    plt.plot([], [], '->', color='red', label='Request')
    if preempted_resources:
        plt.plot([], [], '--', color='purple', label='Preempted')
    plt.legend(loc='best')
    
    plt.axis('off')
    plt.tight_layout()
    
    # Save figure to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    
    # Encode the image
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    
    return img_str

# def plot_matrices(resource_manager):
#     """
#     Plot allocation, max, and need matrices.
    
#     Args:
#         resource_manager: ResourceManager instance
        
#     Returns:
#         str: Base64 encoded PNG image
#     """
#     matrices = resource_manager.get_resource_allocation_matrix()
#     n_processes = len(matrices['processes'])
#     n_resources = len(matrices['available'])
    
#     # Create figure with subplots
#     fig, axs = plt.subplots(1, 3, figsize=(15, 5))
    
#     # Custom colormap from light to dark blue
#     cmap = LinearSegmentedColormap.from_list('blue_cmap', ['#EEEEFF', '#0000AA'])
    
#     # Plot allocation matrix
#     im1 = axs[0].imshow(matrices['allocation'], cmap=cmap)
#     axs[0].set_title('Allocation Matrix')
#     axs[0].set_xlabel('Resource Types')
#     axs[0].set_ylabel('Processes')
#     axs[0].set_xticks(range(n_resources))
#     axs[0].set_yticks(range(n_processes))
#     axs[0].set_xticklabels([f'R{i+1}' for i in range(n_resources)])
#     axs[0].set_yticklabels([f'P{pid}' for pid in matrices['processes']])
    
#     # Add text annotations to allocation matrix
#     for i in range(n_processes):
#         for j in range(n_resources):
#             axs[0].text(j, i, int(matrices['allocation'][i, j]), 
#                         ha="center", va="center", color="black")
    
#     # Plot max matrix
#     im2 = axs[1].imshow(matrices['max'], cmap=cmap)
#     axs[1].set_title('Max Matrix')
#     axs[1].set_xlabel('Resource Types')
#     axs[1].set_xticks(range(n_resources))
#     axs[1].set_yticks(range(n_processes))
#     axs[1].set_xticklabels([f'R{i+1}' for i in range(n_resources)])
#     axs[1].set_yticklabels([f'P{pid}' for pid in matrices['processes']])
    
#     # Add text annotations to max matrix
#     for i in range(n_processes):
#         for j in range(n_resources):
#             axs[1].text(j, i, int(matrices['max'][i, j]), 
#                         ha="center", va="center", color="black")
    
#     # Plot need matrix
#     im3 = axs[2].imshow(matrices['need'], cmap=cmap)
#     axs[2].set_title('Need Matrix')
#     axs[2].set_xlabel('Resource Types')
#     axs[2].set_xticks(range(n_resources))
#     axs[2].set_yticks(range(n_processes))
#     axs[2].set_xticklabels([f'R{i+1}' for i in range(n_resources)])
#     axs[2].set_yticklabels([f'P{pid}' for pid in matrices['processes']])
    
#     # Add text annotations to need matrix
#     for i in range(n_processes):
#         for j in range(n_resources):
#             axs[2].text(j, i, int(matrices['need'][i, j]), 
#                         ha="center", va="center", color="black")
    
#     # Add available resources as text below the plots
#     available_text = "Available Resources: " + ", ".join([f"R{i+1}={val}" for i, val in enumerate(matrices['available'])])
#     fig.text(0.5, 0.02, available_text, ha='center', fontsize=12)
    
#     plt.tight_layout()
#     plt.subplots_adjust(bottom=0.15)
    
#     # Save figure to a bytes buffer
#     buf = io.BytesIO()
#     plt.savefig(buf, format='png', dpi=100)
#     plt.close()
    
#     # Encode the image
#     buf.seek(0)
#     img_str = base64.b64encode(buf.read()).decode('utf-8')
    
#     return img_str


#added extra check
def plot_matrices(resource_manager):
    """
    Plot allocation, max, and need matrices.
    
    Args:
        resource_manager: ResourceManager instance
        
    Returns:
        str: Base64 encoded PNG image
    """
    matrices = resource_manager.get_resource_allocation_matrix()
    n_processes = len(matrices['processes'])
    n_resources = len(matrices['available'])
    
    # Create figure with subplots (adjusted spacing)
    fig, axs = plt.subplots(1, 3, figsize=(15, 5))
    plt.subplots_adjust(wspace=0.4, bottom=0.3)  # Increased spacing and bottom margin
    
    # Custom colormap from light to dark blue
    cmap = LinearSegmentedColormap.from_list('blue_cmap', ['#EEEEFF', '#0000AA'])
    
    # Plot allocation matrix (optimized label placement)
    im1 = axs[0].imshow(matrices['allocation'], cmap=cmap)
    axs[0].set_title('Allocation', pad=10)  # Shorter title
    axs[0].set_xlabel('Resources', labelpad=5)
    axs[0].set_ylabel('Processes', labelpad=5)
    axs[0].set_xticks(range(n_resources))
    axs[0].set_yticks(range(n_processes))
    axs[0].set_xticklabels([f'R{i+1}' for i in range(n_resources)], rotation=45, ha='right')
    axs[0].set_yticklabels([f'P{pid}' for pid in matrices['processes']])
    
    # Add text annotations to allocation matrix (smaller font)
    for i in range(n_processes):
        for j in range(n_resources):
            axs[0].text(j, i, int(matrices['allocation'][i, j]), 
                        ha="center", va="center", color="black", fontsize=9)
    
    # Plot max matrix (optimized)
    im2 = axs[1].imshow(matrices['max'], cmap=cmap)
    axs[1].set_title('Max', pad=10)
    axs[1].set_xlabel('Resources', labelpad=5)
    axs[1].set_xticks(range(n_resources))
    axs[1].set_yticks(range(n_processes))
    axs[1].set_xticklabels([f'R{i+1}' for i in range(n_resources)], rotation=45, ha='right')
    axs[1].set_yticklabels([])  # Remove redundant y-labels
    
    # Add text annotations to max matrix
    for i in range(n_processes):
        for j in range(n_resources):
            axs[1].text(j, i, int(matrices['max'][i, j]), 
                        ha="center", va="center", color="black", fontsize=9)
    
    # Plot need matrix (optimized)
    im3 = axs[2].imshow(matrices['need'], cmap=cmap)
    axs[2].set_title('Need', pad=10)
    axs[2].set_xlabel('Resources', labelpad=5)
    axs[2].set_xticks(range(n_resources))
    axs[2].set_yticks(range(n_processes))
    axs[2].set_xticklabels([f'R{i+1}' for i in range(n_resources)], rotation=45, ha='right')
    axs[2].set_yticklabels([])  # Remove redundant y-labels
    
    # Add text annotations to need matrix
    for i in range(n_processes):
        for j in range(n_resources):
            axs[2].text(j, i, int(matrices['need'][i, j]), 
                        ha="center", va="center", color="black", fontsize=9)
    
    # Add available resources as text below the plots (more compact)
    available_text = "Available: " + " ".join([f"R{i+1}={val}" for i, val in enumerate(matrices['available'])])
    fig.text(0.5, 0.15, available_text, ha='center', fontsize=10)  # Moved higher
    
    plt.tight_layout()
    
    # Save figure to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')  # Added bbox_inches
    plt.close()
    
    # Encode the image
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    
    return img_str




def plot_scheduling_gantt(scheduler):
    """
    Plot Gantt chart for scheduling simulation.
    
    Args:
        scheduler: Scheduler instance with simulation history
        
    Returns:
        str: Base64 encoded PNG image
    """

     # Handle tuple case
    if isinstance(scheduler, tuple):
        scheduler, history = scheduler
    else:
        # Assume it's a scheduler object
        scheduler = scheduler
        history = getattr(scheduler, 'history', [])
    
    if not history:
        return None
        
    # Rest of your existing plotting code...
    # Extract process execution data from history
    process_execution = {}
    current_process = None
    start_time = 0
    
    for step in history:
        time = step['time']
        running = step.get('running', None)
        
        if running != current_process:
            if current_process is not None:
                if current_process not in process_execution:
                    process_execution[current_process] = []
                process_execution[current_process].append((start_time, time))
            
            current_process = running
            start_time = time


    history = scheduler.history
    if not history:
        return None
        
    # Extract process execution data from history
    process_execution = {}
    current_process = None
    start_time = 0
    
    for step in history:
        time = step['time']
        running = step.get('running', None)
        
        if running != current_process:
            if current_process is not None:
                if current_process not in process_execution:
                    process_execution[current_process] = []
                process_execution[current_process].append((start_time, time))
            
            current_process = running
            start_time = time
    
    # Add final process execution
    if current_process is not None:
        if current_process not in process_execution:
            process_execution[current_process] = []
        process_execution[current_process].append((start_time, history[-1]['time'] + 1))
    
    # Create Gantt chart
    fig, ax = plt.subplots(figsize=(12, 5))
    
    # Colors for different processes
    colors = plt.cm.tab10.colors
    
    # Plot bars for each process
    y_ticks = []
    y_labels = []
    
    for i, (pid, intervals) in enumerate(sorted(process_execution.items())):
        y_ticks.append(i)
        y_labels.append(f"P{pid}")
        
        for start, end in intervals:
            ax.barh(i, end - start, left=start, height=0.5, 
                   color=colors[i % len(colors)], alpha=0.8, 
                   edgecolor='black', linewidth=1)
            
            # Add duration label if bar is wide enough
            if end - start > 1:
                ax.text((start + end) / 2, i, f"{end - start}", 
                       ha='center', va='center', color='black')
    
    # Set labels and title
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.set_xlabel('Time')
    ax.set_ylabel('Process')
    
    # Add scheduling algorithm type to title
    scheduler_type = type(scheduler).__name__.replace('Scheduler', '')
    ax.set_title(f'{scheduler_type} Scheduling Gantt Chart')
    
    # Add grid
    ax.grid(axis='x', linestyle='--', alpha=0.7)
    
    # Set x-axis limits
    ax.set_xlim(0, history[-1]['time'] + 1)
    
    # Add completion statistics
    completion_times = {}
    waiting_times = {}
    turnaround_times = {}
    
    for pid, intervals in process_execution.items():
        completion_time = max(end for _, end in intervals)
        execution_time = sum(end - start for start, end in intervals)
        waiting_time = completion_time - execution_time
        
        completion_times[pid] = completion_time
        waiting_times[pid] = waiting_time
        turnaround_times[pid] = completion_time
    
    avg_waiting = sum(waiting_times.values()) / len(waiting_times) if waiting_times else 0
    avg_turnaround = sum(turnaround_times.values()) / len(turnaround_times) if turnaround_times else 0
    
    stats_text = f"Average Waiting Time: {avg_waiting:.2f}\nAverage Turnaround Time: {avg_turnaround:.2f}"
    plt.figtext(0.01, 0.01, stats_text, fontsize=10)
    
    plt.tight_layout()
    
    # Save figure to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    plt.close()
    
    # Encode the image
    buf.seek(0)
    img_str = base64.b64encode(buf.read()).decode('utf-8')
    
    return img_str