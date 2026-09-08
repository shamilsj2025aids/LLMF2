import os
import sys
import json
import time
import argparse
import random
import signal
import multiprocessing
from multiprocessing import Pool, Manager

# Add parent directory to sys.path to import qiga_solver
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from qiga_solver.instance import generate_instance
from qiga_solver.solver import QIGA

# Global event for graceful shutdown
shutdown_event = None

def init_worker(event):
    global shutdown_event
    shutdown_event = event
    # Ignore SIGINT in workers, handle in main
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def generate_instruction(instance):
    n_jobs = len(instance)
    n_machines = len(instance[0])
    
    intros = [
        f"Solve the Job Shop Scheduling Problem (JSSP) for {n_jobs} jobs and {n_machines} machines.",
        f"You are tasked with scheduling {n_jobs} jobs on {n_machines} machines to minimize the total makespan.",
        f"Find the optimal schedule for the following JSSP instance with {n_jobs} jobs and {n_machines} machines.",
        f"Given {n_jobs} jobs to be processed on {n_machines} machines, generate a schedule that minimizes the makespan.",
        f"Determine a job shop schedule to minimize the overall completion time for {n_jobs} jobs across {n_machines} machines."
    ]
    
    details_phrasings = [
        "The operation sequences and their durations (machine_id, processing_time) for each job are as follows:\n",
        "Here are the requirements for each job, formatted as (machine, time):\n",
        "Job specifications (machine, duration) are given below:\n"
    ]
    
    goals = [
        "Your goal is to output a schedule that minimizes the makespan.",
        "Output the final schedule minimizing the maximum completion time.",
        "Provide a structured schedule that achieves the shortest possible makespan."
    ]
    
    instruction = random.choice(intros) + "\n" + random.choice(details_phrasings)
    
    for i, job in enumerate(instance):
        ops_str = ", ".join([f"(M{m}, {t})" for m, t in job])
        instruction += f"Job {i}: {ops_str}\n"
        
    instruction += random.choice(goals)
    return instruction

def solve_instance(seed):
    if shutdown_event and shutdown_event.is_set():
        return None
        
    # Re-seed the local random generator for safety
    random.seed(seed)
    
    n_jobs = random.randint(3, 12)
    n_machines = random.randint(3, 8)
    n_ops = n_jobs * n_machines
    
    instance = generate_instance(n_jobs, n_machines, seed)
    
    generations = max(50, min(300, 20 * n_ops))
    pop_size = max(20, min(60, 4 * n_ops))
    
    solver = QIGA(pop_size=pop_size, generations=generations, seed=seed)
    best_schedule, best_makespan, _ = solver.run(instance)
    
    instruction = generate_instruction(instance)
    
    output_obj = {
        "makespan": best_makespan,
        "schedule": best_schedule
    }
    
    return {
        "instruction": instruction,
        "output": json.dumps(output_obj)
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-size-mb", type=float, default=5120.0, help="Target size in MB")
    parser.add_argument("--target-examples", type=int, default=None, help="Target number of examples")
    parser.add_argument("--dataset-path", type=str, default="dataset.jsonl", help="Path to output jsonl")
    parser.add_argument("--checkpoint-path", type=str, default="checkpoint.json", help="Path to checkpoint json")
    args = parser.parse_args()
    
    dataset_path = args.dataset_path
    checkpoint_path = args.checkpoint_path
    
    examples_completed = 0
    total_elapsed_overall = 0.0
    
    if os.path.exists(dataset_path):
        print(f"Resuming from existing {dataset_path}...")
        # Fast line count
        with open(dataset_path, 'r') as f:
            for _ in f:
                examples_completed += 1
        print(f"Already completed {examples_completed} examples.")
        
    if os.path.exists(checkpoint_path):
        try:
            with open(checkpoint_path, 'r') as f:
                ckpt = json.load(f)
                total_elapsed_overall = ckpt.get("elapsed_time", 0.0)
        except Exception:
            pass
    
    def get_file_size_mb():
        if os.path.exists(dataset_path):
            return os.path.getsize(dataset_path) / (1024 * 1024)
        return 0.0
        
    m = Manager()
    shutdown_evt = m.Event()
    
    def signal_handler(sig, frame):
        print("\nInterrupt received, shutting down gracefully...")
        shutdown_evt.set()
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    cpu_count = multiprocessing.cpu_count()
    print(f"Starting pool with {cpu_count} workers...")
    
    pool = Pool(processes=cpu_count, initializer=init_worker, initargs=(shutdown_evt,))
    
    seed = int(time.time() * 1000) % 1000000 + examples_completed
    
    session_start_time = time.time()
    session_start_examples = examples_completed
    batch_size = cpu_count * 2
    
    try:
        with open(dataset_path, 'a') as f:
            while not shutdown_evt.is_set():
                current_size_mb = get_file_size_mb()
                
                if args.target_examples is not None and examples_completed >= args.target_examples:
                    print(f"Reached target examples ({args.target_examples}). Stopping.")
                    break
                    
                if args.target_examples is None and current_size_mb >= args.target_size_mb:
                    print(f"Reached target size ({current_size_mb:.2f} MB >= {args.target_size_mb} MB). Stopping.")
                    break
                
                seeds = [seed + i for i in range(batch_size)]
                seed += batch_size
                
                # Use imap to yield results as soon as they are ready
                for res in pool.imap_unordered(solve_instance, seeds):
                    if res is None:
                        continue
                    f.write(json.dumps(res) + "\n")
                    f.flush()
                    examples_completed += 1
                    
                    if examples_completed % 50 == 0:
                        session_elapsed = time.time() - session_start_time
                        total_elapsed = total_elapsed_overall + session_elapsed
                        current_size_mb = get_file_size_mb()
                        
                        session_examples = examples_completed - session_start_examples
                        examples_per_sec = session_examples / session_elapsed if session_elapsed > 0 else 0
                        examples_per_hour = examples_per_sec * 3600
                        
                        if args.target_examples is not None:
                            remaining_examples = args.target_examples - examples_completed
                            eta_seconds = remaining_examples / examples_per_sec if examples_per_sec > 0 else 0
                        else:
                            mb_per_example = current_size_mb / examples_completed if examples_completed > 0 else 0
                            remaining_mb = max(0.0, args.target_size_mb - current_size_mb)
                            eta_seconds = (remaining_mb / mb_per_example) / examples_per_sec if examples_per_sec > 0 and mb_per_example > 0 else 0
                            
                        eta_hours = eta_seconds / 3600
                        
                        ckpt_data = {
                            "examples_completed": examples_completed,
                            "elapsed_time": total_elapsed,
                            "current_size_mb": current_size_mb,
                            "examples_per_hour": examples_per_hour,
                            "eta_hours": eta_hours
                        }
                        
                        with open(checkpoint_path, 'w') as cf:
                            json.dump(ckpt_data, cf, indent=4)
                            
                        print(f"[Checkpoint] Examples: {examples_completed} | Size: {current_size_mb:.2f} MB | Rate: {examples_per_hour:.0f} ex/h | ETA: {eta_hours:.2f} h")
                        
    except KeyboardInterrupt:
        print("Keyboard interrupt in main loop.")
        shutdown_evt.set()
    finally:
        pool.close()
        pool.join()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
