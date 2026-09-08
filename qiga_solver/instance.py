import random
import json

def generate_instance(n_jobs, n_machines, seed=None):
    if seed is not None:
        random.seed(seed)
    
    jobs = []
    for _ in range(n_jobs):
        machines = list(range(n_machines))
        random.shuffle(machines)
        job = []
        for m in machines:
            duration = random.randint(1, 20)
            job.append((m, duration))
        jobs.append(job)
    return jobs

def save_instance(instance, filepath):
    with open(filepath, 'w') as f:
        json.dump(instance, f, indent=4)

def load_instance(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)
