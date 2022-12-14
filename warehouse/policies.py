import operator
import random
import string

import requests


AVAILABLE_POLICIES = ('random', 'brain', 'greedy')


class RandomAgent:
    def action(self, state):
        possible_actions = tuple(
            action for action, val in enumerate(state.get('mask'))
            if val == 1
        )
        return {'bin': random.choice(possible_actions)}


class BrainAgent:
    """Poll actions from a deployed brain."""
    def __init__(self, host, port, *, concept_name):
        self.base_url = f'http://{host}:{port}'
        # A client_id is important for keeping brain memory consistent
        # for the same client
        self.client_id = ''.join(
            random.choices(string.ascii_letters + string.digits, k=10)
        )
        self.concept = concept_name

    def action(self, state):
        payload = {'state': state}
        response = requests.post(
            f'{self.base_url}/v2/clients/{self.client_id}/predict', json=payload
        )
        if response.status_code != 200:
            raise ValueError(response.text)
        return response.json()['concepts'][self.concept]['action']


class GreedyAgent:
    """Always select the smallest bin in A."""
    def action(self, state):
        allowed_bins = [
            (i, x)
            for i, (x, y) in enumerate(zip(state['bin_availabilities'], state['mask']))
            if state['next_po']['quantity'] <= x and y > 0
        ]
        try:
            # find best bin in A
            bin_ = [
                i
                for i, _ in sorted(allowed_bins, key=operator.itemgetter(1))
                if i < 6
            ][0]
        except IndexError:
            # find best bin in warehouse
            bin_ = [i for i, _ in sorted(allowed_bins, key=operator.itemgetter(1))][0]
        return {'bin': bin_}


def get_agent(policy: str, **kwargs):
    if policy == 'random':
        return RandomAgent()
    if policy == 'brain':
        return BrainAgent(**kwargs, concept_name='SaturateA')
    if policy == 'greedy':
        return GreedyAgent()
