## Attribution
If you use this logistic model, please provide credit by citing:
Author: Enita Sela  
Thesis: [An Integrated Logistics Model for a Decentralized Biopharmaceutical Manufacturing]  
Year: 2025
License: Mozilla Public License 2.0 (MPL-2.0)  


## Logistics-Model
Logistics Model for a Decentralized Biopharmaceutical Manufacturing

Biopharmaceutical manufacturing has traditionally relied on centralized production mod­els, which are efficient for mass production, but pose challenges in responding to local­ized health crises and increasing environmental concerns. The COVID­19 pandemic ex­posed the rigidity of centralized supply chains, emphasizing the need for more flexible and sustainable approaches. This thesis explores the implementation of Mobile On De­mand (MOD) biopharmaceutical manufacturing as an alternative decentralized production model, focusing on the logistical optimization and environmental assessment of MOD de­ployment for COVID­19 vaccine production in Berlin.
A two-­stage stochastic programming model was developed to optimize the placement and routing of MOD units, incorporating Monte Carlo simulations to handle demand un­certainty. The model was converted into a Mixed Integer Programming (MIP) formula­tion and solved using an L­-shaped decomposition algorithm, leveraging real hospital data from Berlin to ensure practical feasibility. Demand estimation evolved across multiple iterations, transitioning from hospitalization estimates to real vaccination rates, significantly impacting deployment strategies and associated costs.

## Problem Definition and Scope
# Spatial and Temporal Considerations
By implementing decentralize and flexible manufacturing, the MOD system aims to ad­ dress the limitations represented by a centralized pharmaceutical production: while cen­ tralize facilities can produce vaccines in bulk, they are less responsive to sudden localized demand spikes, in contrast with MOD’s framework.
The problem’s spatial dimension involves a network of Berlin hospitals that serves as both deployment bases and also demand points.These hospitals are represented as nodes in the logistic network. The hospital distribution across the city is as follows:
• Northwest: 19 hospitals • Southwest: 19 hospitals • Northeast: 10 hospitals • Southeast: 4 hospitals
Due to the proximity of some hospitals, deploying separate MOD units to each facility would be inefficient from a time and cost point of view. Instead, hospitals are aggregate into ”super nodes” based on geographical clustering to optimize the setup and routing decisions.
The temporal dimension considers multiple periods, accounting for: the setup and deploy­ ment of each MOD unit at the beginning of a period; vaccine production during each period, considering the capacity of deployed MOD units; movement of MOD units between super nodes at the end of a period if relocation is necessary; demand evolution over multiple periods, influencing MOD positioning.
The primary source of uncertainty in this problem is vaccine demand, which fluctuates based on infection rates, public health policies, and population needs. Demand esti­ mates are derived from the COVID­19 incidence data as reported in the situation report of 19/04/2023 [Robert Koch Institute. Coronavirus Disease 2019 (COVID­19) Daily Situation Re­ port by the Robert Koch Institute. 2023. URL: https://www.rki.de/DE/Home/ homepage_node.html.] , proportioned to Berlin’s population.

Monte Carlo Scenario Generation
A Monte Carlo simulation is used to generate a set of demand scenarios. These scenarios take into account fluctuations in demand due to factors like infection rate variations, public health interventions, and seasonal effects.
The scenario generation process follows these steps:
• Historical demand data is obtained from Robert Koch Institute (RKI) reports [15].
• Statisticaldistributions(Gaussian)isfittedtothehistoricaldatatoestimateprobable future demand patterns.
• A large number of demand realizations are sampled using Monte Carlo methods.
• Thesampleddemandscenariosareclusteredintoarepresentativesubsettoensure computational tractability while maintaining variability.
Each generated scenario is assigned a probability ps, ensuring that the optimization model accounts for a range of possible demand levels. This scenario approach enhances the robustness pf the entire system.

# Demand Modeling Across Different Codes
The demand modeling evolved across the three versions of the code:
• Code 1: model without the implementation of the L­shaped algorithm and the de­ mand is based on hospitalization rates.
• Code 2: model with implementation of the L­shaped algorithm and the demand is based on hospitalization rates.
• Code 3: model with the implementation of the L­shaped algorithm and the demand is based on real vaccination rates.
