import networkx as nx
import random

def bankers_algorithm(processes, resources, allocation, max_need, available):
    work = available.copy()
    finish = {p: False for p in processes}
    safe_sequence = []

    while True:
        allocated_in_this_round = False
        for p in processes:
            if not finish[p]:
                if all((max_need[p][r] - allocation[p][r]) <= work[r] for r in resources):
                    for r in resources:
                        work[r] += allocation[p][r]
                    finish[p] = True
                    safe_sequence.append(p)
                    allocated_in_this_round = True
        if not allocated_in_this_round:
            break

    if all(finish.values()):
        return True, safe_sequence
    else:
        return False, []
