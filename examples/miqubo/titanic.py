import itertools
import os

import dimod
import matplotlib.pyplot as plt
import neal
import numpy as np
import pandas as pd

from dwave.embedding.chimera import find_clique_embedding
from dwave.system import DWaveSampler, FixedEmbeddingComposite

plt.figure()

datapath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'data',
                        'formatted_titanic.csv')
dataset = pd.read_csv(datapath)


def prob(dataset):
    """Joint probability distribution for the given data."""

    # bin by the number of different values
    num_rows, num_columns = dataset.shape
    bins = [len(np.unique(dataset[:, ci])) for ci in range(num_columns)]

    prob, _ = np.histogramdd(dataset, bins)
    return prob / np.sum(prob)


def shannon_entropy(p):
    p = p.flatten()
    return -sum(pi*np.log2(pi) for pi in p if pi)


def conditional_shannon_entropy(p, *conditional_indices):
    """entropy of P conditional on variable j"""

    axis = tuple(i for i in np.arange(len(p.shape)) if i not in conditional_indices)

    return shannon_entropy(p) - shannon_entropy(np.sum(p, axis=axis))


def mutual_information(prob, j):
    """mutual information between all variables and variable j"""
    return shannon_entropy(np.sum(prob, axis=j)) - conditional_shannon_entropy(prob, j)


def conditional_mutual_information(p, j, *conditional_indices):
    """mutual information between all variables (X) and variable j (Y), conditional on k (Z)"""
    return conditional_shannon_entropy(np.sum(p, axis=j), *conditional_indices) - conditional_shannon_entropy(p, j, *conditional_indices)


scores = {}
for feature in dataset.columns:

    if feature == 'survived':
        continue

    scores[feature] = mutual_information(prob(dataset[['survived', feature]].values), 0)

labels, values = zip(*sorted(scores.items(), key=lambda pair: pair[1], reverse=True))


plt.subplot(1, 2, 1)
plt.bar(np.arange(len(labels)), values)
plt.xticks(np.arange(len(labels)), labels, rotation=90)


# build qubo
features = list(set(dataset.columns).difference(('survived',)))


bqm = dimod.BinaryQuadraticModel.empty(dimod.BINARY)

# add the features
for feature in features:
    mi = mutual_information(prob(dataset[['survived', feature]].values), 1)
    bqm.add_variable(feature, -mi)


for f0, f1 in itertools.combinations(features, 2):
    mi = conditional_mutual_information(prob(dataset[['survived', f0, f1]].values), 1, 2)
    bqm.add_interaction(f0, f1, -mi)

bqm.normalize()  # to -1, 1


# need to create a QPU sampler that can solve this problem
qpu_sampler = DWaveSampler(solver={'qpu': True})

embedding = find_clique_embedding(bqm.variables,
                                  16, 16, 4,  # size of the chimera lattice
                                  target_edges=qpu_sampler.edgelist)

sampler = FixedEmbeddingComposite(qpu_sampler, embedding)


selected_features = np.zeros((len(features), len(features)))
for k in range(1, len(features) + 1):
    kbqm = bqm.copy()
    kbqm.update(dimod.generators.combinations(bqm, k, strength=6))

    # sample = sampler.sample(kbqm, num_reads=10000).first.sample
    sample = dimod.ExactSolver().sample(kbqm).first.sample

    for fi, f in enumerate(features):
        selected_features[k-1, fi] = sample[f]

plt.subplot(1, 2, 2)
plt.imshow(selected_features)
plt.ylabel('number of features')
plt.xticks(np.arange(len(features)), features, rotation=90)

plt.show()
