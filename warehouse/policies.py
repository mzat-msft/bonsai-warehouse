import random


AVAILABLE_POLICIES = ('random',)


class RandomAgent:
    def action(self, state):
        possible_actions = tuple(
            action for action, val in enumerate(state.get('mask'))
            if val is True
        )
        return {'bin': random.choice(possible_actions)}


def get_agent(policy: str):
    if policy == 'random':
        return RandomAgent()
