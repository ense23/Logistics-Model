import pandas as pd
from pyomo.environ import *
from pyomo.opt import SolverFactory
import numpy as np
import random

# Load Berlin hospital data and cluster into 14 supernodes
berlin_hospitals = pd.read_csv("/Users/enitasela/Desktop/Finale/BerlinHospitals.csv")

# Define parameters for clustering hospitals into supernodes
supernodes = {i: [] for i in range(1, 15)}  # Dictionary to store hospitals in each cluster
hospital_coords = berlin_hospitals[['Latitude', 'Longitude']].values  # Extract coordinates

# Clustering based on proximity (hospitals within 5 km are grouped)
def cluster_hospitals():
    from scipy.spatial.distance import pdist, squareform
    dist_matrix = squareform(pdist(hospital_coords, metric='euclidean'))
    cluster_id = 1
    assigned = set()
    
    for i in range(len(hospital_coords)):
        if i in assigned:
            continue
        
        if cluster_id > 14:  # Ensure we do not exceed 14 clusters
            closest_cluster = min(supernodes.keys(), key=lambda x: len(supernodes[x]))
            supernodes[closest_cluster].append(i)
        else:
            supernodes[cluster_id].append(i)
            assigned.add(i)
            for j in range(len(hospital_coords)):
                if j not in assigned and dist_matrix[i, j] < 0.05:  # 5 km in degrees
                    supernodes[cluster_id].append(j)
                    assigned.add(j)
            cluster_id += 1

cluster_hospitals()

# Monte Carlo Demand Calculation based on Berlin COVID incidence rates- hospitalized patiants
berlin_population = 3_700_000  # Berlin population
seven_day_incidence = 21.6  # Cases per 100,000 people
hospitalization_rate = 6.42 / 21.6  # Probability of hospitalization per case

def generate_stochastic_demand():
    base_demand = berlin_population * (seven_day_incidence / 100000) * hospitalization_rate
    demand_scenario = {
        s: {n: int(random.gauss(base_demand, base_demand * 0.2)) for n in range(1, 15)} for s in range(1, 101)
    }
    return demand_scenario

demand_scenario = generate_stochastic_demand()

# Parameters
MOD_daily_capacity = 10000  # Daily vaccine production capacity for each MOD unit
campaign_duration = 60  # Campaign duration
fixed_deployment_cost = 5000  # Fixed cost per MOD deployment (EUR)
travel_cost_per_km = 1  # Travel cost per km (EUR)
penalty_cost_unmet_demand = 100  # Penalty for unmet demand per unit (EUR)

# Define Model
model = ConcreteModel()
T = range(1, 4)  # Time periods
S = range(1, 101)  # 100 Monte Carlo Scenarios
N = range(1, 15)  # 14 Supernodes
MODS = range(1, 5)  # Mobile units

# Decision Variables
model.deploy = Var(N, MODS, T, S, within=Binary)
model.move = Var(N, N, MODS, T, S, within=Binary)
model.production = Var(N, MODS, T, S, within=NonNegativeReals)
model.unmet_demand = Var(N, S, T, within=NonNegativeReals)

# Objective Function (Minimize Total Cost Per Scenario)
model.scenario_cost = Var(S, within=NonNegativeReals)

def scenario_cost_rule(m, s):
    return m.scenario_cost[s] == (
        sum(fixed_deployment_cost * model.deploy[n, m, t, s] for n in N for m in MODS for t in T) +
        sum(travel_cost_per_km * model.move[i, j, m, t, s] for i in N for j in N for m in MODS for t in T if i != j) +
        sum(penalty_cost_unmet_demand * model.unmet_demand[n, s, t] for n in N for t in T)
    )
model.cost_constraint = Constraint(S, rule=scenario_cost_rule)
model.objective = Objective(expr=sum(model.scenario_cost[s] for s in S) / len(S), sense=minimize)

# Constraints
model.deploy_limit = ConstraintList()
for s in S:
    for m in MODS:
        for t in T:
            model.deploy_limit.add(sum(model.deploy[n, m, t, s] for n in N) <= 1)

model.prod_capacity = ConstraintList()
for s in S:
    for n in N:
        for m in MODS:
            for t in T:
                model.prod_capacity.add(model.production[n, m, t, s] <= MOD_daily_capacity * campaign_duration * model.deploy[n, m, t, s])

model.demand_sat = ConstraintList()
for s in S:
    for n in N:
        for t in T:
            model.demand_sat.add(
                sum(model.production[n, m, t, s] for m in MODS) + model.unmet_demand[n, s, t] >= demand_scenario[s][n]
            )

# Solve for best scenario
opt = SolverFactory('gurobi')
best_scenario, best_cost = None, float('inf')
best_deployment = []

for s in S:
    results = opt.solve(model, tee=True)
    scenario_cost = model.scenario_cost[s].value
    if scenario_cost < best_cost:
        best_cost, best_scenario = scenario_cost, s
        best_deployment = [(n, m, t) for n in N for m in MODS for t in T if model.deploy[n, m, t, s].value > 0.5]

# Output best scenario
output_file = "optimized_deployment_resultsFIN.txt"
with open(output_file, "w") as file:
    file.write(f"Optimization Completed\nBest Scenario: {best_scenario}\nTotal Cost: {best_cost:.2f} EUR\n")
    for (n, m, t) in best_deployment:
        file.write(f"Deploy MOD{m} at Super Node {n} in Period {t}\n")

print(f"Optimized results saved to {output_file}")
