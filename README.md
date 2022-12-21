# Warehouse placement optimization

## Problem statement

Product orders (PO)s arrive sequentially at a warehouse facility and have to be stored.
The objective is to maximize occupation of one area of the warehouse, because
it is quicker to pick products from that area when orders have to be shipped.

The warehouse is composed of different bins. Each bin has an assigned
capacity and can contain only products with the same properties. In this
implementation we consider only one property: the product type.

The sequence of POs arriving at the warehouse is known beforehand, so
that one can decide where best to store a product given what's coming next.
For instance, imagine that we have to store 5 and 6 units of product *x* and there are two
bins with availability 5 and 8. Knowing the sequence of arriving POs,
we will store the 5 units in the smaller bin and the 6 units later in the
larger.

This is a constraint optimization problem that resembles the [bin
packing problem](https://en.wikipedia.org/wiki/Bin_packing_problem#Online_heuristics).


## The simulation


In the simulation we have the following setup. There are two warehouse areas
named ``A`` and ``B``. We want to maximize the occupation of area ``A``.
In each area there are 6 bins with different capacities.
There are three types of products: ``x``, ``y`` and ``z``.
At each step of the simulation a PO is taken from the sequence of POs and an
agent decides in which bin to store the product.

The number of warehouse areas and the number of bins are hardcoded in the
sim. The reason is that the bins are all possible actions for the agent, and
a Bonsai brain must have a static action space. Adding or removing bins
changes the action space.
Product types are hardcoded too, but there is no technical reason for this.
That is, one could easily add or remove a product type and no change to the
brain architecture would be needed.

The simulation starts with a configuration that provides the initial
occupation for the bins and the list of incoming POs. It also provides
the maximum number of items to allocate for each episode.
An episode ends when no more POs need to be allocated or when there are
no more bins available.


## Running the simulation

The simulation can be launched in unmanaged fashion by running the following
command in the root of the repository after installing all dependencies
listed in ``requirements.txt``:

```sh
python -m warehouse
```

To let Bonsai manage the simulation one can build the attached Dockerfile and
add the simulator in their Bonsai's workspace.


## Implemented solutions


All solutions are implemented in ``warehouse/policies.py``. They can be
evaluated on a dataset of different scenarios with the following command:
```sh
python -m warehouse --policy $POLICY --scenarios data/scenarios.jsonl -e -1
```
where ``$POLICY`` should be replaced by the name of the policy to evaluate.


### Random

``$POLICY=random`` This policy selects randomly the bin where to store the
incoming product


### Greedy

``$POLICY=greedy`` This policy selects the bin in area ``A`` with the lowest
number of available spots, if present. If not, it selects the same in area
``B``. This tends to maximize usage of area ``A`` but it does not use any
knowledge on which POs are coming next.


### Optimal

``$POLICY=optimal`` This policy applies a modified version of the
quasi-optimal solution to the bin packing problem. The incoming items are
sorted in decreasing order with respect to their size. Then the items are
looped and each product is assigned to a bin in ``A`` that fits or, if none is
available, it's stored in a bin in ``B``. When selecting the best bin we
make two passes. In the first pass we assign the item to the smallest bin
that fits, and in the second pass we assign the bin to the largest bin that
fits. We do this because we observed that using only the first pass does not
always provide a solution able to fit as many items as possible.


### Brain

``$POLICY=brain`` This policy is used to test a brain trained with Bonsai.


## Evaluating the solutions

We evaluate the brain on 10'000 episodes, each containing 10 POs to
allocate and different configuration for the initial bins occupations.

Our KPIs are the occupation of area ``A``, as a percentage of its total
capacity, and the amount of POs that the agent was not able to allocate into
the warehouse. We compute the average of these KPIs over the whole set of
episodes.

The results we obtain for the implemented policies are summarized in the
table below. For completeness, we also report the occupation of area ``B``
as a percentage of its total capacity.

| Policy                       | ``A`` | ``B`` | Leftovers |
| ---------------------------- |:-----:|:-----:|:---------:|
| Random                       | 0.51  | 0.49  | 11.01     |
| Greedy                       | 0.56  | 0.40  | 10.82     |
| Optimal                      | 0.58  | 0.41  | 10.06     |
