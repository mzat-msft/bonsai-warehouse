import json

from warehouse.sim import AVAILABLE_BINS, get_random_po


def init_bins():
    for bin_ in AVAILABLE_BINS:
        po = get_random_po(bin_.capacity)
        yield {'bin': bin_.code, 'product': po.product.sku, 'quantity': po.quantity}


def init_pos():
    for _ in range(20):
        po = get_random_po(10)
        yield {
            'product': po.product.sku,
            'quantity': po.quantity,
        }


def generate_scenario():
    bins = [bin_ for bin_ in init_bins()]
    return {
        'total_pos': 10,
        'init_bins': bins,
        'pos': [po for po in init_pos()],
    }


def generate_scenarios(episodes):
    with open('scenarios.json', 'w') as fp:
        for _ in range(episodes):
            scenario = generate_scenario()
            fp.write(json.dumps(scenario))
            fp.write('\n')
