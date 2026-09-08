import time
import json
from instance import generate_instance
from solver import QIGA
from visualize import plot_gantt, plot_convergence

def main():
    print("Generating demo instance (6 jobs, 5 machines, seed=42)...")
    instance = generate_instance(n_jobs=6, n_machines=5, seed=42)
    
    print("Running QIGA Solver (pop_size=40, generations=150)...")
    solver = QIGA(pop_size=40, generations=150, seed=42)
    
    start_time = time.time()
    best_schedule, best_makespan, history = solver.run(instance)
    runtime = time.time() - start_time
    
    print(f"Total Runtime: {runtime:.2f} seconds")
    print(f"Best Makespan: {best_makespan}")
    
    print("Saving plots...")
    plot_gantt(best_schedule, best_makespan, "gantt.png")
    plot_convergence(history, "convergence.png")
    
    print("Saving final results to JSON...")
    output_data = {
        "instance": instance,
        "schedule": best_schedule,
        "makespan": best_makespan,
        "runtime": runtime
    }
    with open("demo_results.json", "w") as f:
        json.dump(output_data, f, indent=4)
        
    print("Done! Check gantt.png, convergence.png, and demo_results.json.")

if __name__ == "__main__":
    main()
