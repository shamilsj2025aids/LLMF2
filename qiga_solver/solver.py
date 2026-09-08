import math
import random

class QIGA:
    def __init__(self, pop_size, generations, seed=None):
        self.pop_size = pop_size
        self.generations = generations
        if seed is not None:
            random.seed(seed)
        
    def _initialize_population(self, num_genes):
        # Initialize angles to pi/4, so probability is 0.5
        return [[math.pi / 4.0 for _ in range(num_genes)] for _ in range(self.pop_size)]
        
    def _observe(self, individual):
        observed_bits = []
        probabilities = []
        for theta in individual:
            prob_1 = math.sin(theta) ** 2
            bit = 1 if random.random() < prob_1 else 0
            observed_bits.append(bit)
            probabilities.append(prob_1)
        return observed_bits, probabilities

    def _decode_schedule(self, instance, job_sequence):
        n_jobs = len(instance)
        n_machines = len(instance[0])
        
        # Track next operation index for each job
        job_op_indices = [0] * n_jobs
        
        # Track when each machine is next available
        machine_avail_time = [0] * n_machines
        # Track when each job is next available
        job_avail_time = [0] * n_jobs
        
        schedule = []
        
        for job_id in job_sequence:
            op_idx = job_op_indices[job_id]
            machine_id, duration = instance[job_id][op_idx]
            
            start_time = max(machine_avail_time[machine_id], job_avail_time[job_id])
            end_time = start_time + duration
            
            schedule.append({
                "job": job_id,
                "operation_index": op_idx,
                "machine": machine_id,
                "start": start_time,
                "end": end_time
            })
            
            machine_avail_time[machine_id] = end_time
            job_avail_time[job_id] = end_time
            job_op_indices[job_id] += 1
            
        makespan = max(machine_avail_time)
        return schedule, makespan
        
    def _update_angles(self, pop, observed_pop, best_bits):
        # Standard QEA rotation gate update
        # If best bit is 1 and current bit is 0, we want to increase probability of 1 (increase theta)
        # If best bit is 0 and current bit is 1, we want to decrease probability of 1 (decrease theta)
        # Assuming theta in [0, pi/2], delta_theta > 0 moves towards 1
        delta = 0.05 * math.pi
        
        new_pop = []
        for ind_idx, individual in enumerate(pop):
            new_ind = []
            obs_bits = observed_pop[ind_idx]
            for j, theta in enumerate(individual):
                b = obs_bits[j]
                b_best = best_bits[j]
                
                # Logic:
                # if b == 0 and b_best == 1: theta should increase
                # if b == 1 and b_best == 0: theta should decrease
                # else: no change
                
                d_theta = 0
                if b == 0 and b_best == 1:
                    d_theta = delta
                elif b == 1 and b_best == 0:
                    d_theta = -delta
                    
                new_theta = theta + d_theta
                # clip to [0, pi/2]
                new_theta = max(0.0, min(math.pi / 2.0, new_theta))
                new_ind.append(new_theta)
            new_pop.append(new_ind)
        return new_pop

    def run(self, instance):
        n_jobs = len(instance)
        n_machines = len(instance[0])
        num_genes = n_jobs * n_machines
        
        # Base template: [0,0.., 1,1.., n-1,n-1..]
        base_template = []
        for i in range(n_jobs):
            base_template.extend([i] * n_machines)
            
        population = self._initialize_population(num_genes)
        
        best_makespan = float('inf')
        best_schedule = None
        best_bits = None
        
        convergence_history = []
        
        for gen in range(self.generations):
            observed_pop = []
            current_best_makespan = float('inf')
            
            for ind in population:
                obs_bits, probs = self._observe(ind)
                observed_pop.append(obs_bits)
                
                # Pair base template with priority
                # Priority: (bit, probability) - higher is better
                prioritized_template = []
                for i in range(num_genes):
                    priority = (obs_bits[i], probs[i])
                    prioritized_template.append((priority, base_template[i]))
                
                # Sort descending by priority
                prioritized_template.sort(key=lambda x: x[0], reverse=True)
                
                # Extract the job sequence
                job_sequence = [item[1] for item in prioritized_template]
                
                # Decode
                schedule, makespan = self._decode_schedule(instance, job_sequence)
                
                if makespan < best_makespan:
                    best_makespan = makespan
                    best_schedule = schedule
                    best_bits = obs_bits
                    
            convergence_history.append(best_makespan)
            
            # Update angles towards the best bits
            population = self._update_angles(population, observed_pop, best_bits)
            
        return best_schedule, best_makespan, convergence_history
