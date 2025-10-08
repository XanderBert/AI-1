#!/usr/bin/env python3
from game.dino import *
from game.agent import Agent


class ObstaclesHelper:

    jump_threshold = 80

    @staticmethod
    def get_first_in_front(game) -> Optional[Obstacle]:
        dino_right = game.dino.x + game.dino.MAX_WIDTH
        right_obstacles = [o for o in game.obstacles if o.rect.x > dino_right]
        if right_obstacles:
            return min(right_obstacles, key=lambda o: o.rect.x)
        return None

    @staticmethod
    def get_most_left(game) -> Optional[Obstacle]:
        visible = [o for o in game.obstacles if o.rect.x + o.rect.width >= 0]
        if visible:
            return min(visible, key=lambda o: o.rect.x)
        return None

    @staticmethod
    def get_distance(o, game) -> float:
        return o.rect.x - game.dino.x

    @staticmethod
    def get_distance_from_right(o, game) -> float:
        return o.rect.x - (game.dino.x + game.dino.MAX_WIDTH)

    @staticmethod
    def is_object_under(o, game) -> bool:
        dino_left = game.dino.x
        dino_right = game.dino.x + game.dino.MAX_WIDTH
        obs_left = o.rect.x
        obs_right = o.rect.x + o.rect.width
        return obs_left < dino_right and obs_right > dino_left

    @staticmethod
    def is_behind(o, game) -> bool:
        return o.rect.x + o.rect.width < game.dino.x


class State:
    @staticmethod
    def should_transition(game) -> str:
        raise NotImplementedError

    @staticmethod
    def get_action(game) -> DinoMove:
        raise NotImplementedError

class IdleState(State):
    @staticmethod
    def should_transition(game) -> str:
        o = ObstaclesHelper.get_first_in_front(game)
        if not o:
            return None
        
        dist = ObstaclesHelper.get_distance_from_right(o, game)
        
        if o.type.y >= 300 and dist < ObstaclesHelper.jump_threshold:
            return "jump"
        elif o.type.y < 300 and dist < 120:
            return "duck"
        return None

    @staticmethod
    def get_action(game) -> DinoMove:
        return DinoMove.NO_MOVE


class JumpState(State):
    @staticmethod
    def should_transition(game) -> str:
        
        # Go back to idle when dino lands
        if game.dino.state == DinoState.RUNNING:
            return "idle"
        return None

    @staticmethod
    def get_action(game) -> DinoMove:
        return DinoMove.UP


class DuckState(State):
    @staticmethod
    def should_transition(game) -> str:
        # Duck for short time, then return to idle
        o = ObstaclesHelper.get_first_in_front(game)
        if not o or ObstaclesHelper.is_behind(o, game):
            return "idle"
        return None

    @staticmethod
    def get_action(game) -> DinoMove:
        return DinoMove.DOWN


class MyAgent(Agent):

    states = {
        "idle": IdleState(),
        "jump": JumpState(),
        "duck": DuckState()
    }

    current_state = states["idle"]

    @staticmethod
    def transition_to(state_name: str) -> None:
        if state_name in MyAgent.states:
            MyAgent.current_state = MyAgent.states[state_name]

    @staticmethod
    def update(game) -> None:
        next_state = MyAgent.current_state.should_transition(game)
        if next_state:
            MyAgent.transition_to(next_state)

    @staticmethod
    def get_move(game: Game) -> DinoMove:
        MyAgent.update(game)
        return MyAgent.current_state.get_action(game)
