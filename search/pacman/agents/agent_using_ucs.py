#!/usr/bin/env python3
from game.controllers import PacManControllerBase
from game.pacman import Game, DM, Direction
from typing import List
import sys
from os.path import dirname
import numpy as np

# hack for importing from parent package
sys.path.append(dirname(dirname(dirname(__file__))))
from search_templates import Problem, Solution
from ucs import ucs

epsilon = 0.1 

class PacProblem(Problem):
    def __init__(self, game: Game, target_node: int = None) -> None:
        self.game: Game = game
        self.target_node: int = target_node

    # --- Other Problem methods (initial_state, actions, result, is_goal) remain as they were ---
    def initial_state(self):
        return (self.game.pac_loc)
    
    def actions(self, state) -> List[int]:
        current_location = state
        valid_actions = []
        for action in [Direction.UP, Direction.RIGHT, Direction.DOWN, Direction.LEFT]:
            next_loc = self.game.get_neighbor(current_location, action)
            if next_loc != current_location: 
                valid_actions.append(action)
        return valid_actions

    def result(self, state, action: int):
        loc = state
        next_loc = self.game.get_neighbor(loc, action)
        return (next_loc)

    def is_goal(self, state) -> bool:
        if self.target_node is None:
            return False 
        return state == self.target_node 
    
    # --- OPTIMIZED COST FUNCTION ---
    def cost(self, state, action: int) -> float:
        loc = state
        next_loc = self.game.get_neighbor(loc, action)
        BASE_COST = 1.0  # Base cost of moving one step

        danger_cost = 0.0
        ghost_reward = 0.0
        
        # Determine the immediate threat or opportunity
        min_dangerous_distance = float("inf")
        
        for g in range(self.game.NUM_GHOSTS):
            ghost_loc = self.game.get_ghost_loc(g)
            distance = self.game.get_path_distance(next_loc, ghost_loc)

            if distance == -1 or distance == 0:
                continue # Ignore invalid distances
            
            if self.game.is_edible(g):
                # 1. EAT REWARD: If we can eat the ghost on this move, give a massive reward.
                if distance <= self.game.EAT_DISTANCE:
                    # Give an extremely high negative cost (reward)
                    ghost_reward -= 50000.0 
            else:
                # 2. FLEE PENALTY: Track the closest dangerous ghost
                min_dangerous_distance = min(min_dangerous_distance, distance)



        # --- Combine Costs ---
        total = BASE_COST + danger_cost + ghost_reward

        return max(total, BASE_COST)




class Agent_Using_UCS(PacManControllerBase):
    last_dir = Direction.NONE

    def tick(self, game: Game) -> None:
        current = game.pac_loc
        
      
        
        targets = []

        # Collect all pill locations
        targets.extend(game.get_active_pills_nodes())
        targets.extend(game.get_active_power_pills_nodes())

        # Check for edible ghosts
        is_power_pill_active = any(game.is_edible(g) for g in range(game.NUM_GHOSTS))

        if is_power_pill_active:
            edible_ghost_locs = [
                game.get_ghost_loc(g) 
                for g in range(game.NUM_GHOSTS) 
                if game.is_edible(g)
            ]
            targets.extend(edible_ghost_locs)

        if not targets:
            targets.append(game.get_initial_pacman_position())


        nearest_target = game.get_target(current, targets, True, DM.PATH)


        # 2. Final check and UCS execution
        if nearest_target is None:
             return
            
        prob = PacProblem(game, target_node=nearest_target)
        sol = ucs(prob)

        # 3. Execute the move
        if sol and sol.actions:
            self.pacman.set(sol.actions[0])
            self.last_dir = sol.actions[0] 
        else:
            # Fallback to the last successful direction or a legal turn
            legal_dirs = game.get_possible_pacman_dirs(include_reverse=False)
            if self.last_dir in legal_dirs:
                self.pacman.set(self.last_dir)
            elif legal_dirs:
                self.pacman.set(legal_dirs[0])
   