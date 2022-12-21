import abc
import operator
import random
import string
from copy import deepcopy
from itertools import chain

import requests

AVAILABLE_POLICIES = ('brain', 'greedy', 'optimal', 'random')


class BaseAgent(abc.ABC):
    """Base class for implementing an agent that solves the warehouse optimization."""
    @abc.abstractmethod
    def action(self, state):
        """Return the best action for the given state."""

    def reset(self):
        """Reset the agent."""


class RandomAgent(BaseAgent):
    def action(self, state):
        possible_actions = tuple(
            action for action, val in enumerate(state.get('mask'))
            if val == 1
        )
        return {'bin': random.choice(possible_actions)}


class BrainAgent(BaseAgent):
    """Poll actions from a deployed brain."""
    def __init__(self, host, port, *, concept_name):
        self.base_url = f'http://{host}:{port}'
        # A client_id is important for keeping brain memory consistent
        # for the same client
        self.concept = concept_name
        self.set_client_id()

    def set_client_id(self):
        self.client_id = ''.join(
            random.choices(string.ascii_letters + string.digits, k=10)
        )

    def action(self, state):
        payload = {'state': state}
        response = requests.post(
            f'{self.base_url}/v2/clients/{self.client_id}/predict', json=payload
        )
        if response.status_code != 200:
            raise ValueError(response.text)
        return response.json()['concepts'][self.concept]['action']

    def reset(self):
        response = requests.delete(f'{self.base_url}/v2/clients/{self.client_id})')
        if response.status_code != 204:
            raise ValueError(response.text)
        self.set_client_id()


class GreedyAgent(BaseAgent):
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


class OptimalAgent(BaseAgent):
    """Apply optimal bin packing problem solution."""
    def __init__(self):
        self.solution = None

    @staticmethod
    def assign_bins(pos, warehouse, rev_order_bins=False):
        ordered_pos = sorted(
            (
                (i, po)
                for i, po in enumerate(pos)
            ),
            key=lambda x: x[1]['quantity'],
            reverse=True
        )
        assignments = []
        for i, po in ordered_pos:
            sorted_bins = sorted(
                (
                    (key, val['quantity'])
                    for key, val in warehouse.items()
                    if val['product'] == po['product']
                    and val['capacity'] - val['quantity'] >= po['quantity']
                ),
                key=operator.itemgetter(1),
                reverse=rev_order_bins,
            )
            try:
                optimal_bin = [
                    bin_ for bin_, _ in sorted_bins if bin_.startswith('A')
                ].pop()
            except IndexError:
                optimal_bin = sorted_bins.pop()[0]
            warehouse[optimal_bin]['quantity'] += po['quantity']
            warehouse[optimal_bin]['product'] = po['product']
            assignments.append((i, optimal_bin))
        return assignments

    def solve(self, state):
        pos = list(chain([state['next_po']], state['coming_pos']))
        while True:
            try:
                wh = deepcopy(state['warehouse'])
                assignments = self.assign_bins(pos, wh)
                break
            except IndexError:
                try:
                    wh = deepcopy(state['warehouse'])
                    assignments = self.assign_bins(pos, wh, True)
                    break
                except IndexError:
                    pos.pop()

        solution = [
            bin_
            for _, bin_ in sorted(assignments, key=operator.itemgetter(0), reverse=True)
        ]
        return solution

    def action(self, state):
        if self.solution is None:
            self.solution = self.solve(state)
        map_bin_to_id = {
            'A1': 0,
            'A2': 1,
            'A3': 2,
            'A4': 3,
            'A5': 4,
            'A6': 5,
            'B1': 6,
            'B2': 7,
            'B3': 8,
            'B4': 9,
            'B5': 10,
            'B6': 11,
        }
        try:
            return {'bin': map_bin_to_id[self.solution.pop()]}
        except IndexError:
            return {'bin': state['mask'].index(1)}

    def reset(self):
        """Reset the agent."""
        self.solution = None


def get_agent(policy: str, **kwargs) -> BaseAgent:
    if policy == 'random':
        return RandomAgent()
    if policy == 'brain':
        return BrainAgent(**kwargs, concept_name='SaturateA')
    if policy == 'greedy':
        return GreedyAgent()
    if policy == 'optimal':
        return OptimalAgent()
    raise ValueError(f'Unknown policy {policy}')
