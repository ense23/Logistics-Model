import pandas as pd
from pyomo.environ import *
from pyomo.opt import SolverFactory
import numpy as np
import random
from scipy.spatial.distance import pdist, squareform

# ------------------------------- Data Loading -------------------------------
berlin_hospitals = pd.read_csv("path.csv")
hospital_coords = berlin_hospitals[['Latitude', 'Longitude']].values  

# Clustering hospitals into 14 supernodes (5 km proximity)
supernodes = {i: [] for i in range(1, 15)}
dist_matrix = squareform(pdist(hospital_coords, metric='euclidean'))

assigned = set()
cluster_id = 1
for i in range(len(hospital_coords)):
    if i in assigned:
        continue
    if cluster_id > 14:
        closest_cluster = min(supernodes.keys(), key=lambda x: len(supernodes[x]))
        supernodes[closest_cluster].append(i)
    else:
        supernodes[cluster_id].append(i)
        assigned.add(i)
        for j in range(len(hospital_coords)):
            if j not in assigned and dist_matrix[i, j] < 0.05:  
                supernodes[cluster_id].append(j)
                assigned.add(j)
        cluster_id += 1

# ------------------------------- Demand Generation -------------------------------
berlin_population = 3_700_000  
seven_day_incidence = 21.6  
hospitalization_rate = 6.42 / 21.6  

def generate_stochastic_demand():
    base_demand = berlin_population * (seven_day_incidence / 100000) * hospitalization_rate
    return {
        s: {n: max(100, int(random.gauss(base_demand, base_demand * 0.2))) for n in range(1, 15)}
        for s in range(1, 101)
    }

demand_scenario = generate_stochastic_demand()

# ------------------------------- Model Parameters -------------------------------
MOD_daily_capacity = 10000  
campaign_duration = 60  
fixed_deployment_cost = 5000  
travel_cost_per_km = 1  
penalty_cost_unmet_demand = 100  

# ------------------------------- Master Problem Definition -------------------------------
master = ConcreteModel()

T = range(1, 4)  
S = range(1, 101)  
N = range(1, 15)  
MODS = range(1, 5)  

# Decision Variables
master.deploy = Var(N, MODS, T, within=Binary)
master.move = Var(N, N, MODS, T, within=Binary)
master.theta = Var(S, within=NonNegativeReals)  

# Objective Function
master.objective = Objective(
    expr=sum(fixed_deployment_cost * master.deploy[n, m, t] for n in N for m in MODS for t in T) +
         sum(travel_cost_per_km * master.move[i, j, m, t] for i in N for j in N for m in MODS for t in T if i != j) +
         sum(master.theta[s] for s in S) / len(S),
    sense=minimize
)

# Constraints
master.deploy_limit = ConstraintList()
for m in MODS:
    for t in T:
        master.deploy_limit.add(sum(master.deploy[n, m, t] for n in N) >= 1)

master.move_constraint = ConstraintList()
for m in MODS:
    for t in T:
        for i in N:
            for j in N:
                if i != j:
                    master.move_constraint.add(master.move[i, j, m, t] <= master.deploy[i, m, t])

master.optimality_cuts = ConstraintList()

# ------------------------------- L-Shaped Algorithm -------------------------------
opt = SolverFactory('gurobi')
convergence = False
output_file = "LShaped_ResultsSMFIN.txt"

best_scenario = None
best_total_cost = float('inf')
best_deployment = {}
best_production = {}
best_demand = {}

with open(output_file, "w") as file:
    while not convergence:
        print("Solving Master Problem...")
        file.write("Solving Master Problem...\n")
        master_results = opt.solve(master, tee=True)

        convergence = True  

        for s in S:
            subproblem = ConcreteModel()

            # Decision Variables
            subproblem.production = Var(N, MODS, T, within=NonNegativeReals)
            subproblem.unmet_demand = Var(N, T, within=NonNegativeReals)

            # Objective Function
            subproblem.objective = Objective(
                expr=sum(penalty_cost_unmet_demand * subproblem.unmet_demand[n, t] for n in N for t in T),
                sense=minimize
            )

            # Demand Satisfaction
            subproblem.demand_sat = ConstraintList()
            for n in N:
                for t in T:
                    subproblem.demand_sat.add(
                        sum(subproblem.production[n, m, t] for m in MODS) + subproblem.unmet_demand[n, t] >= demand_scenario[s][n]
                    )

            # Production Capacity
            subproblem.production_capacity = ConstraintList()
            for n in N:
                for m in MODS:
                    for t in T:
                        subproblem.production_capacity.add(
                            subproblem.production[n, m, t] <= master.deploy[n, m, t].value * MOD_daily_capacity
                        )

            print(f"Solving Subproblem for Scenario {s}...")
            file.write(f"Solving Subproblem for Scenario {s}...\n")
            subproblem_results = opt.solve(subproblem, tee=True)

            scenario_cost = sum(penalty_cost_unmet_demand * subproblem.unmet_demand[n, t].value for n in N for t in T)

            if scenario_cost < best_total_cost:
                best_total_cost = scenario_cost
                best_scenario = s

                best_deployment = {
                    (n, m, t): master.deploy[n, m, t].value
                    for n in N for m in MODS for t in T if master.deploy[n, m, t].value > 0.5
                }
                best_production = {
                    (n, m, t): subproblem.production[n, m, t].value
                    for n in N for m in MODS for t in T if subproblem.production[n, m, t].value > 0
                }
                best_demand = demand_scenario[s]  

    file.write("\nOptimization Completed\n")
    file.write(f"Best Scenario: {best_scenario}\n")
    file.write(f"Total Cost: {best_total_cost:.2f} EUR\n")

    file.write("\nDemand Per Supernode (Best Scenario):\n")
    for n in N:
        for t in T:
            file.write(f"Super Node {n}, Period {t}: {best_demand[n]:.0f} doses required\n")

    file.write("\nDeployment Decisions:\n")
    for (n, m, t), val in best_deployment.items():
        file.write(f"Deploy MOD{m} at Super Node {n} in Period {t}\n")

    file.write("\nVaccine Production:\n")
    for (n, m, t), val in best_production.items():
        file.write(f"MOD{m} produced {val:.0f} doses at Super Node {n} in Period {t}\n")

print("L-Shaped Algorithm Optimization Completed")
