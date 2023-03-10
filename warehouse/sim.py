import dataclasses
import random
from collections import OrderedDict
from typing import Dict, List, Optional

from bonsai_connector.connector import BonsaiEventType


@dataclasses.dataclass
class Product:
    sku: str


AVAILABLE_PRODUCTS = (
    Product('x'),
    Product('y'),
    Product('z'),
)


@dataclasses.dataclass
class PO:
    product: Product
    quantity: int


@dataclasses.dataclass
class Bin:
    area: str
    code: str
    capacity: int
    occupation: int = 0
    product: Optional[Product] = None

    @property
    def availability(self):
        return self.capacity - self.occupation

    @property
    def empty(self):
        return self.availability == self.capacity

    def store_po(self, po: PO):
        if self.product is not None and po.product != self.product:
            raise ValueError(f'Product in {po} must be same type as in {self}')
        if po.quantity + self.occupation > self.capacity:
            raise ValueError(f'Not enough capacity for {po} in {self}')

        if po.quantity > 0:
            self.product = po.product
            self.occupation += po.quantity

    def to_state(self):
        try:
            product = AVAILABLE_PRODUCTS.index(self.product)
        except ValueError:
            product = -1
        return {
            'capacity': self.capacity,
            'quantity': self.occupation,
            'product': product,
        }


class Warehouse:
    def __init__(self, bins: List[Bin]):
        self._bins = OrderedDict({bin_.code: bin_ for bin_ in bins})
        self.areas = set(bin_.area for bin_ in bins)

    @property
    def bins(self):
        return self._bins.values()

    def idx_to_bin(self, idx):
        return list(self.bins)[idx].code

    def store_po(self, bin_, po):
        self._bins[bin_].store_po(po)

    def to_state(self):
        return {
            bin_.code: bin_.to_state()
            for bin_ in self._bins.values()
        }


AVAILABLE_BINS = [
    Bin('A', 'A1', 10),
    Bin('A', 'A2', 15),
    Bin('A', 'A3', 5),
    Bin('A', 'A4', 20),
    Bin('A', 'A5', 20),
    Bin('A', 'A6', 20),
    Bin('B', 'B1', 20),
    Bin('B', 'B2', 10),
    Bin('B', 'B3', 4),
    Bin('B', 'B4', 4),
    Bin('B', 'B5', 10),
    Bin('B', 'B6', 6),
]


def get_random_po(max_quantity):
    return PO(random.choice(AVAILABLE_PRODUCTS), random.randint(1, max_quantity))


def get_planned_pos(max_quantity, total_pos):
    return [get_random_po(max_quantity) for _ in range(total_pos)]


class Simulation:
    next_po: PO
    config: Dict
    pos: List
    _state: Dict

    def __init__(self):
        self.warehouse = Warehouse(AVAILABLE_BINS)

    @property
    def interface(self):
        return {
            'name': 'Warehouse Placement',
            'description': {
                'action': {
                    'category': 'Struct',
                    'fields': [
                        {
                            'name': 'bin',
                            'type': {
                                'category': 'Number',
                                'namedValues': [
                                    {'name': bin_.code, 'value': i}
                                    for i, bin_ in enumerate(self.warehouse.bins)
                                ] +
                                [
                                    {'name': 'None', 'value': len(self.warehouse.bins)}
                                ],
                            },
                            'comment': 'Where to store the next po',
                        }
                    ],
                },
                'state': {
                    'category': 'Struct',
                    'fields': [
                        {
                            'name': 'bin_availabilities',
                            'type': {
                                'category': 'Array',
                                'length': len(self.warehouse.bins),
                                'type': {'category': 'Number'},
                            }
                        },
                        {
                            'name': 'next_po',
                            'type': {
                                'category': 'Struct',
                                'fields': [
                                    {
                                        'name': 'product',
                                        'type': {
                                            'category': 'Number',
                                            'namedValues': [
                                                {'name': product.sku, 'value': i}
                                                for i, product in enumerate(AVAILABLE_PRODUCTS)  # noqa
                                            ]
                                        },
                                    },
                                    {
                                        'name': 'quantity',
                                        'type': {'category': 'Number'}
                                    }
                                ]
                            }
                        },
                        {
                            'name': 'coming_pos',
                            'type': {
                                'category': 'Array',
                                'length': 10,
                                'type': {
                                    'category': 'Struct',
                                    'fields': [
                                        {
                                            'name': 'product',
                                            'type': {
                                                'category': 'Number',
                                                'namedValues': [
                                                    {'name': product.sku, 'value': i}
                                                    for i, product in enumerate(AVAILABLE_PRODUCTS)  # noqa
                                                ]
                                            },
                                        },
                                        {
                                            'name': 'quantity',
                                            'type': {'category': 'Number'}
                                        },
                                    ]
                                }
                            }
                        },
                        *[
                            {
                                'name': area,
                                'type': {'category': 'Number'}
                            }
                            for area in self.warehouse.areas
                        ],
                        {
                            'name': 'mask',
                            'type': {
                                'category': 'Array',
                                'length': len(self.warehouse.bins) + 1,
                                'type': {'category': 'Number'}
                            }
                        },
                        {
                            'name': 'available_bins',
                            'type': {'category': 'Number'}
                        },
                    ]
                },
                'config': {
                    'category': 'Struct',
                    'fields': [
                        {
                            'name': 'total_pos',
                            'type': {'category': 'Number'}
                        },
                        {
                            'name': 'max_quantity',
                            'type': {'category': 'Number'}
                        },
                        {
                            'name': 'max_quantity_initial',
                            'type': {'category': 'Number'}
                        },
                        {
                            'name': 'init_bins',
                            'type': {
                                'category': 'Struct',
                                'fields': [
                                    {
                                        'name': bin_.code,
                                        'type': {
                                            'category': 'Struct',
                                            'fields': [
                                                {
                                                    'name': 'product',
                                                    'type': {
                                                        'category': 'String',
                                                        'values': [product.sku for product in AVAILABLE_PRODUCTS]  # noqa
                                                    },
                                                },
                                                {
                                                    'name': 'quantity',
                                                    'type': {
                                                        'category': 'Number',
                                                        'start': 0,
                                                        'stop': bin_.capacity,
                                                        'step': 1,
                                                    },
                                                },
                                            ]
                                        }
                                    }
                                    for bin_ in self.warehouse.bins
                                ]
                            }
                        },
                        {
                            'name': 'pos',
                            'comment': 'Make this array long enough to complete an episode',  # noqa
                            'type': {
                                'category': 'Array',
                                'length': 20,
                                'type': {
                                    'category': 'Struct',
                                    'fields': [
                                        {
                                            'name': 'product',
                                            'type': {
                                                'category': 'String',
                                                'values': [product.sku for product in AVAILABLE_PRODUCTS]  # noqa
                                            }
                                        },
                                        {
                                            'name': 'quantity',
                                            'type': {'category': 'Number'}
                                        }
                                    ]
                                }
                            }
                        }
                    ]
                }
            }
        }

    def init_warehouse(self):
        if init_bins := self.config.get('init_bins'):
            for bin_, bin_content in init_bins.items():
                product = Product(bin_content['product'])
                if product not in AVAILABLE_PRODUCTS:
                    raise ValueError(f'Product {product} not in available products')
                po = PO(product, bin_content['quantity'])
                self.warehouse.store_po(bin_, po)
        else:
            print('Init config for bins not found. Generating randomly...')
            for bin_ in self.warehouse.bins:
                max_quantity = self.config['max_quantity']
                po = get_random_po(
                    max_quantity if max_quantity < bin_.capacity else bin_.capacity
                )
                bin_.store_po(po)

    def init_planned_pos(self):
        if init_pos := self.config.get('pos'):
            pos = []
            for entry in reversed(init_pos):
                product = Product(entry['product'])
                if product not in AVAILABLE_PRODUCTS:
                    raise ValueError(f'Product {product} not in available products')
                pos.append(PO(product, entry['quantity']))
        else:
            print('Init POs plan not found. Generating randomly...')
            pos = get_planned_pos(
                self.config['max_quantity'], 2 * self.config['total_pos'] + 1
            )
        if len(pos) < self.config['total_pos']:
            raise ValueError(
                'Not enough POs provided. '
                f'Minimum {self.config["total_pos"]} got {len(pos)}.'
            )
        self.pos = pos

    def empty_warehouse(self):
        for bin_ in self.warehouse.bins:
            bin_.product = None
            bin_.occupation = 0

    def set_next_po(self):
        try:
            self.next_po = self.pos.pop()
        except IndexError:
            self.next_po = PO(random.choice(AVAILABLE_PRODUCTS), 0)

    def compute_mask(self):
        mask = [
            (
                bin_.availability >= self.next_po.quantity and
                (
                    bin_.product == self.next_po.product or
                    bin_.empty
                )
            )
            for bin_ in self.warehouse.bins
        ]
        if sum(mask) > 0:
            mask.append(False)
        else:
            mask.append(True)
        return mask

    @property
    def state(self):
        return self._state

    def update_state(self):
        coming_pos = [
            {'product': AVAILABLE_PRODUCTS.index(po.product), 'quantity': po.quantity}
            for po in reversed(self.pos[-10:])
        ]
        bin_avail = []
        area_occs = {}
        area_caps = {}
        for bin_ in self.warehouse.bins:
            bin_avail.append(bin_.availability)
            area_occs[bin_.area] = area_occs.get(bin_.area, 0) + bin_.occupation
            area_caps[bin_.area] = area_caps.get(bin_.area, 0) + bin_.capacity
        for area in area_occs:
            area_occs[area] /= area_caps[area]
        struct_po = {
            'product': AVAILABLE_PRODUCTS.index(self.next_po.product),
            'quantity': self.next_po.quantity
        }
        mask = self.compute_mask()
        self._state = {
            "bin_availabilities": bin_avail,
            "next_po": struct_po,
            "mask": mask,
            "available_bins": sum(mask[:-1]),
            "coming_pos": coming_pos,
            **area_occs,
            "remaining_products": len(self.pos),
            "warehouse": self.warehouse.to_state(),
            "halted": False,
        }

    def episode_start(self, config):
        self.config = config
        print('Intializing episode...')
        print('Config:', self.config)
        self.empty_warehouse()
        self.init_warehouse()
        self.init_planned_pos()
        self.set_next_po()
        self.update_state()
        return self.state

    def episode_step(self, action):
        if action['bin'] == 12:
            return self.state
        try:
            store_bin = self.warehouse.idx_to_bin(int(action['bin']))
        except ValueError:
            store_bin = action['bin']
        self.warehouse.store_po(bin_=store_bin, po=self.next_po)
        self.set_next_po()
        self.update_state()
        return self.state

    def episode_finish(self, content):
        print(f'Episode ended: {content}')

    def dispatch_event(self, next_event):
        if next_event.event_type == BonsaiEventType.EPISODE_START:
            return self.episode_start(next_event.event_content)
        elif next_event.event_type == BonsaiEventType.EPISODE_STEP:
            return self.episode_step(next_event.event_content)
        elif next_event.event_type == BonsaiEventType.EPISODE_FINISH:
            return self.episode_finish(next_event.event_content)
        elif next_event.event_type == BonsaiEventType.IDLE:
            print("Idling")
            return
        else:
            raise RuntimeError(
                f"Unexpected BonsaiEventType. Got {next_event.event_type}"
            )
