import argparse
import json
import statistics

from bonsai_connector import BonsaiConnector

from warehouse.policies import AVAILABLE_POLICIES, get_agent
from warehouse.scenario_generator import generate_scenarios
from warehouse.sim import Simulation

parser = argparse.ArgumentParser(description="Run a simulation")
parser.add_argument('-p', '--policy', choices=AVAILABLE_POLICIES)
parser.add_argument('-g', '--generate-scenarios', action='store_true')
parser.add_argument('-e', '--episodes', type=int, default=100)
parser.add_argument('--scenarios', type=str)
parser.add_argument(
    '--host', type=str, default='localhost', help='Host of deployed brain'
)
parser.add_argument('--port', type=int, default=5000, help='Port of deployed brain')


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


def clean_state(state):
    cleaned_state = state.copy()
    cleaned_state['mask'] = [int(val) for val in state['mask']]
    return cleaned_state


def evaluate(policy, scenarios, host, port, episodes):
    warehouse_sim = Simulation()
    agent = get_agent(policy, host=host, port=port)
    kpis = {
        'A': [],
        'B': [],
        'leftovers': [],
    }

    with open(scenarios, 'r') as fp:
        scenarios = fp.readlines()

    if episodes < 0:
        episodes = len(scenarios)

    for scenario in scenarios[:episodes]:
        config = json.loads(scenario)
        state = clean_state(warehouse_sim.episode_start(config))
        leftover = 0

        for _ in range(config['total_pos']):
            if state['available_bins'] <= 0:
                leftover = state['remaining_products']
                break
            action = agent.action(state)
            state = clean_state(warehouse_sim.episode_step(action))
        kpis['A'].append(state['A'])
        kpis['B'].append(state['B'])
        kpis['leftovers'].append(leftover)
        agent.reset()

    for key, val in kpis.items():
        print(f'{key}: ', statistics.mean(val))


def main():
    args = parser.parse_args()
    if args.policy:
        evaluate(
            policy=args.policy,
            scenarios=args.scenarios,
            host=args.host,
            port=args.port,
            episodes=args.episodes,
        )
    elif args.generate_scenarios:
        generate_scenarios(args.episodes)
    else:
        train()


if __name__ == '__main__':
    main()
