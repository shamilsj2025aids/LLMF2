# QIGA JSSP Solver

This module solves the Job-Shop Scheduling Problem (JSSP) using a Quantum-Inspired Genetic Algorithm (QIGA). 

## Background
The JSSP can be formulated as a Quadratic Unconstrained Binary Optimization (QUBO) problem, typically solved using quantum annealers or QAOA on gate-based quantum computers. In QUBO, decision variables often represent binary choices such as $x_{i, j, t} = 1$ if operation $j$ of job $i$ starts at time $t$. However, representing complex scheduling problems in QUBO requires a massive number of variables and penalty terms for constraints.

This module uses a **Quantum-Inspired Genetic Algorithm (QIGA)** instead of physical quantum hardware. QIGA maintains the concept of quantum superposition by representing chromosomes as a sequence of "Q-bits" (probability amplitudes). By rotating these amplitudes towards successful classical observations (elitist update), the algorithm achieves a balance of exploration and exploitation, often converging faster than classical genetic algorithms while executing efficiently on classical computers.

## Usage

To run the demonstration:

```bash
python demo.py
```

This will:
1. Generate a $6 \times 5$ JSSP instance.
2. Run the QIGA solver.
3. Save the results (makespan, runtime, instance, and schedule) to `demo_results.json`.
4. Generate `gantt.png` and `convergence.png` for visualization.
