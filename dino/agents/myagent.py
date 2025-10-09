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
    def __init__(self):
        self.tracked: Optional[Obstacle] = None


    def on_enter(self, game, obstacle):
        self.tracked = obstacle  # fix: set as instance variable

    def should_transition(self, game):
        raise NotImplementedError

    def get_action(self, game) -> DinoMove:
        raise NotImplementedError



class IdleState(State):
    def should_transition(self, game):
        o = ObstaclesHelper.get_first_in_front(game)
        if not o:
            return

        dist = ObstaclesHelper.get_distance_from_right(o, game)
        dino_duck_top = Dino.Y_DUCK  # top of the dino when ducking
        obs_bottom = o.type.y + o.type.height

        # Jump if cactus or high obstacle
        if o.type.y >= 300 and dist < ObstaclesHelper.jump_threshold:
            MyAgent.transition_to("jump", game, o)
            print(f"Jump over {o.type.name}")

        # Duck if bird AND we fit under it
        elif "BIRD" in o.type.name and dist < 150:
            if dino_duck_top > obs_bottom:
                MyAgent.transition_to("duck", game, o)
                print(f"Ducking under {o.type.name}")
            else:
                # too low, must jump instead
                MyAgent.transition_to("jump", game, o)
                print(f"Jumping over low {o.type.name}")

            


    def get_action(self, game) -> DinoMove:
        return DinoMove.NO_MOVE



class JumpState(State):
    def should_transition(self, game):
        # Go back to idle when dino lands
        if game.dino.state == DinoState.RUNNING:
            MyAgent.transition_to("idle", game, None)
            return

        # If we’re tracking an obstacle and it’s behind, maybe return to idle
        if self.tracked and ObstaclesHelper.is_behind(self.tracked, game):
            MyAgent.transition_to("idle", game, None)

    def get_action(self, game) -> DinoMove:
        return DinoMove.UP_RIGHT



class DuckState(State):
    def should_transition(self, game):

        # Go to idle if the tracked object is behind
        if self.tracked and ObstaclesHelper.is_behind(self.tracked, game):
            MyAgent.transition_to("idle", game, None)

        # Go back to idle when dino lands (were not tracking a object)
        if game.dino.state == DinoState.RUNNING:
            MyAgent.transition_to("idle", game, None)

    def get_action(self, game) -> DinoMove:
        return DinoMove.DOWN



class MyAgent(Agent):
    states = {
        "idle": IdleState(),
        "jump": JumpState(),
        "duck": DuckState()
    }

    current_state = states["idle"]

    @staticmethod
    def transition_to(state_name: str, game=None, obstacle=None) -> None:
        if state_name in MyAgent.states:
            MyAgent.current_state = MyAgent.states[state_name]
            MyAgent.current_state.on_enter(game, obstacle)
            print(state_name)

        
    @staticmethod
    def get_move(game: Game) -> DinoMove:
        MyAgent.current_state.should_transition(game)
        return MyAgent.current_state.get_action(game)
