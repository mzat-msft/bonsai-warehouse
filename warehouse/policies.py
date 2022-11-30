import random
import string

import requests


AVAILABLE_POLICIES = ('random', 'brain')


class RandomAgent:
    def action(self, state):
        possible_actions = tuple(
            action for action, val in enumerate(state.get('mask'))
            if val is True
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


def get_agent(policy: str, **kwargs):
    if policy == 'random':
        return RandomAgent()
    if policy == 'brain':
        return BrainAgent(**kwargs, concept_name='SaturateA')
