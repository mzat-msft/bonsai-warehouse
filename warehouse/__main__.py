import argparse
import random

from bonsai_connector import BonsaiConnector

from warehouse.policies import AVAILABLE_POLICIES, get_agent
from warehouse.sim import Simulation


parser = argparse.ArgumentParser(description="Run a simulation")
parser.add_argument('-p', '--policy', choices=AVAILABLE_POLICIES)
parser.add_argument('-e', '--episodes', type=int, default=100)


def train():
    warehouse_sim = Simulation()
    with BonsaiConnector(warehouse_sim.interface) as agent:
        state = None
        while True:
            if state is None:
                state = {'halted': False}
            event = agent.next_event(state)
            print(event)
            state = warehouse_sim.dispatch_event(event)
            print(state)


def evaluate(policy, episodes):
    warehouse_sim = Simulation()
    agent = get_agent(policy)
    for _ in range(episodes):
        config = {
            'total_pos': 10,
            'max_quantity': random.choice(range(1, 11)),
            'max_quantity_initial': random.choice(range(1, 6)),
        }
        state = warehouse_sim.episode_start(config)
        for _ in range(config['total_pos']):
            if state['available_bins'] <= 0:
                continue
            action = agent.action(state)
            state = warehouse_sim.episode_step(action)


def main():
    args = parser.parse_args()
    if args.policy:
        evaluate(policy=args.policy, episodes=args.episodes)
    else:
        train()


if __name__ == '__main__':
    main()
