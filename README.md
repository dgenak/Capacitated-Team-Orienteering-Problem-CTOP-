# Capacitated-Team-Orienteering-Problem-CTOP-

## Description

The Capacitated Team Orienteering Problem (CTOP) models the situation of a last-mile delivery company that doesn't have enough vehicle capacity to fulfill all of its orders in a single day. It must therefore decide which packages to deliver, and in what order, so as to maximize the company's total profit.

Each customer has an order volume (demand) and offers a certain profit (profit). The company operates a fleet of K homogeneous vehicles, each with a maximum capacity Q and a strict shift time limit T_max. All routes start and end at the depot (node 0).

The objective is to maximize the total profit collected from served customers. In case of a tie in profit, the solution with the lower total travel time is preferred.

## Constraints
Every vehicle starts and ends its route at the depot (node 0).
Each customer can be served at most once, by a single vehicle; serving all customers is not required.
The total demand of the customers on a route must not exceed the vehicle's capacity Q.
The total travel time/distance of a route, including the return to the depot, must not exceed the shift time limit T_max.
Some customers (e.g. premium accounts, urgent deliveries) are mandatory and must be included in the solution.

## Two problem scenarios
Standard CTOP — no mandatory-node constraint; customers can be freely selected.
Mandatory CTOP — the solution must include every node flagged as mandatory, otherwise it is considered infeasible.

## Input data

The file ctop_main_instance.txt contains:
- Number of nodes |N|, number of vehicles K, capacity Q, time limit T_max
- List of profits per node
- List of demands per node
- Binary list (1 = mandatory node, 0 = optional)
- Square time/distance matrix c_ij between all nodes

# Solution Approach

The solver combines a greedy construction heuristic with a Local Search (LS) procedure and two metaheuristics — Iterated Local Search (ILS) and Large Neighborhood Search (LNS) — to progressively improve the initial solution within the time budget.

## 1. Construction — Greedy Insertion

An initial feasible solution is built by greedy_build(): candidate customers are ranked by profit-to-demand ratio (descending), and each is inserted at the position (route and index) that adds the least extra cost, provided capacity Q and time limit T_max are respected. For the mandatory scenario, mandatory nodes are always placed at the front of the candidate list so they are prioritized during insertion.

## 2. Local Search

local_search() applies a sequence of neighborhood moves until no further improvement is found:

2-opt (two_opt) — reverses route segments to reduce travel cost/time.
Or-opt (or_opt) — relocates a single customer to a better position, either within the same route or into a different one.
Profit-swap (money_is_everything) — replaces a low-profit customer already in a route with a higher-profit unvisited one, whenever the swap keeps the route feasible. Mandatory nodes are never removed by this move.
Greedy re-insertion (greedy_insert_pool) — attempts to insert any remaining unvisited customers (mandatory ones prioritized) into the best available slot across all routes.

## 3. Iterated Local Search (ILS)

ILS_seed() repeatedly perturbs the current best solution — removing a random subset of non-mandatory customers (perturb()) and reinserting them greedily — then re-applies local search. If the resulting solution improves total profit, it becomes the new incumbent; otherwise the search continues from the previous state. After a number of iterations without improvement, the perturbation strength (n_rem) is randomized to escape local optima.

## 4. Large Neighborhood Search (LNS)

LNS() performs a stronger destroy-and-repair cycle: it identifies the routes with the worst profit/cost ratio, removes a randomized number of their (non-mandatory) customers along with additional low profit/demand-ratio nodes network-wide, then rebuilds using greedy insertion combined with a pool of high-ratio unvisited candidates, followed by local search. Solutions are accepted if they don't worsen the incumbent, with a small probability (5%) of accepting a worse solution to diversify the search.

## 5. Feasibility Checking

einai_swsto() validates every candidate solution against all problem constraints: routes start/end at the depot, time limit T_max, capacity Q, each customer visited at most once, and — when applicable — full coverage of all mandatory nodes.

Both Problem 1 (Standard CTOP) and Problem 2 (Mandatory CTOP) follow this same pipeline; the mandatory scenario additionally passes priority_first (sorted mandatory nodes) and mandatory_nodes through construction, local search, and both metaheuristics so mandatory customers are prioritized and protected from removal.

Parameters
Parameter	Problem 1	Problem 2
Random seed	4	8
ILS iterations	100	2,400
LNS iterations	100	200

Seeds and iteration counts were selected empirically after multiple trial runs, balancing solution quality against the 5-minute runtime limit per problem.

## Output

Final routes are written to solution_no_mandatory.txt and solution_mandatory.txt, one route per line as space-separated node indices (starting and ending with 0).
