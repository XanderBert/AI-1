#!/usr/bin/env python3
from search_templates import Problem, Solution
from typing import Optional
from collections import defaultdict
import heapq 

def ucs(prob: Problem) -> Optional[Solution]:
    """Return Solution of the problem solved by UCS search."""
    initial_state = prob.initial_state()
 
    # {state: (parent_state, action_to_reach_state, minimum_path_cost)}
    parent_map = {} 
    parent_map[initial_state] = (None, None, 0.0)
    
    # Stores tuples: (path_cost, state)
    open_list = [(0.0, initial_state)] 

    destination_node = None

    while open_list:
        # Get the node with the LOWEST path cost using heap pop
        current_cost, current_state = heapq.heappop(open_list)

        # If we've already found a better or equal path to this
        # state, skip processing this more expensive one.
        # This handles cases where a state is added multiple times to the queue.
        if current_cost > parent_map.get(current_state, (None, None, float('inf')))[2]:
             continue
        
        # Check for goal
        if prob.is_goal(current_state):
            destination_node = current_state
            break
  
        # Check all available actions
        for action in prob.actions(current_state):
            
            # Determine the resulting state and the cost of the step
            next_state = prob.result(current_state, action)
            step_cost = prob.cost(current_state, action)
            new_path_cost = current_cost + step_cost

            # Check if this state has not been visited OR if we found a cheaper path
            # to this state
            existing_cost = parent_map.get(next_state, (None, None, float('inf')))[2]
            if new_path_cost < existing_cost: 

                # Store the *new, cheaper* path info
                parent_map[next_state] = (current_state, action, new_path_cost)
                
                # Add the state with the new, lower cost to the priority queue
                heapq.heappush(open_list, (new_path_cost, next_state))
                



    if destination_node is None:
        print("Did not found UCS path")
        return None # No solution found


    # Path Reconstruction
    path_actions = []
    
    # Total cost is retrieved from the minimum cost stored in parent_map
    path_cost = parent_map[destination_node][2] 
    
    current_state = destination_node
    
    # Backtrack until the initial state
    while current_state != initial_state:
        parent_state, action, _ = parent_map[current_state]

        # Prepend the action
        path_actions.insert(0, action)
        
        # Move to the parent state
        current_state = parent_state

    return Solution(path_actions, destination_node, path_cost)