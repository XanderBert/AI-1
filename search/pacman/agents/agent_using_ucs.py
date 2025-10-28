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


class PacProblem(Problem):
    def __init__(self, game: Game, target_node: int = None) -> None:
        self.game: Game = game
        self.target_node: int = target_node

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
    
    def cost(self, state, action: int) -> float:
        current_location = state
        next_loc = self.game.get_neighbor(current_location, action)
        
        COST = 100.0  # base movement cost
    
        for g in range(self.game.NUM_GHOSTS):
            ghost_loc = self.game.get_ghost_loc(g)
    
            current_distance = self.game.get_path_distance(current_location, ghost_loc)
            next_distance = self.game.get_path_distance(next_loc, ghost_loc)
    
            if current_distance <= 0 or next_distance <= 0:
                continue
            
            moving_closer = next_distance < current_distance
    
            # Inverse distance weighting: closer ghosts have bigger effect
            danger_weight = max(0.1, 10 / current_distance)
    
            if moving_closer:
                if self.game.is_edible(g):
                    COST -= 50 * danger_weight
                elif current_distance < 18:
                    COST += 500 * danger_weight

        return max(COST, 0)
    
    
    
    
class Agent_Using_UCS(PacManControllerBase):
    last_dir = Direction.NONE

    def tick(self, game: Game) -> None:
        current = game.pac_loc
        targets = []

        # --- Collect all targets ---
        targets.extend(game.get_active_pills_nodes())
        targets.extend(game.get_active_power_pills_nodes())

        # Add edible ghosts as possible targets
        for g in range(game.NUM_GHOSTS):
            if game.is_edible(g):
                targets.append(game.get_ghost_loc(g))

        # Fallback if no targets left
        if not targets:
            targets.append(game.get_initial_pacman_position())


        # Limit search to N nearest pills by raw distance
        N = 3
        targets = sorted(targets, key=lambda t: game.get_path_distance(current, t))[:N]


        # --- Evaluate all targets with UCS ---
        best_sol = None
        best_cost = float("inf")

        for target in targets:
            prob = PacProblem(game, target_node=target)
            sol = ucs(prob)
            if sol is not None and sol.path_cost < best_cost:
                best_sol = sol
                best_cost = sol.path_cost

        # --- Execute best action ---
        if best_sol and best_sol.actions:
            self.pacman.set(best_sol.actions[0])
            self.last_dir = best_sol.actions[0]
        else:
            # fallback behavior if UCS fails
            legal_dirs = game.get_possible_pacman_dirs(include_reverse=False)
            if self.last_dir in legal_dirs:
                self.pacman.set(self.last_dir)
            elif legal_dirs:
                self.pacman.set(legal_dirs[0])