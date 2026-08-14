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
