import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def plot_gantt(schedule, makespan, filepath):
    fig, ax = plt.subplots(figsize=(10, 6))
    
    jobs = list(set([item["job"] for item in schedule]))
    colors = list(mcolors.TABLEAU_COLORS.values())
    job_colors = {job: colors[i % len(colors)] for i, job in enumerate(jobs)}
    
    machines = list(set([item["machine"] for item in schedule]))
    machines.sort(reverse=True) # highest machine at top
    
    for item in schedule:
        job = item["job"]
        machine = item["machine"]
        start = item["start"]
        end = item["end"]
        duration = end - start
        
        ax.barh(machine, duration, left=start, color=job_colors[job], edgecolor='black', alpha=0.8)
        ax.text(start + duration / 2, machine, f"J{job}-O{item['operation_index']}", 
                ha='center', va='center', color='white', fontsize=8, fontweight='bold')
                
    ax.set_yticks(machines)
    ax.set_yticklabels([f"Machine {m}" for m in machines])
    ax.set_xlabel("Time")
    ax.set_title(f"JSSP Gantt Chart (Makespan: {makespan})")
    ax.grid(axis='x', linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()

def plot_convergence(history, filepath):
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(range(1, len(history) + 1), history, marker='o', markersize=4, linestyle='-', color='b')
    ax.set_xlabel("Generation")
    ax.set_ylabel("Best Makespan")
    ax.set_title("QIGA Convergence History")
    ax.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)
    plt.close()
