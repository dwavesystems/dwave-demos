import itertools
import os

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import numpy as np
import pandas as pd

# D-Wave Ocean tools
import dimod
import neal
from dwave.embedding.chimera import find_clique_embedding
from dwave.system import DWaveSampler, FixedEmbeddingComposite

# Read the feature-engineered data into a pandas dataframe
datapath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'data',
                        'formatted_titanic.csv')
dataset = pd.read_csv(datapath)

# Define MI calculations
def prob(dataset):
    """Joint probability distribution for the given data."""

    # bin by the number of different values
    num_rows, num_columns = dataset.shape
    bins = [len(np.unique(dataset[:, ci])) for ci in range(num_columns)]

    prob, _ = np.histogramdd(dataset, bins)
    return prob / np.sum(prob)

def shannon_entropy(p):
    """Shannon entropy H(X) is the sum of P(X)log(P(X)) for probabilty distribution P(X)."""
    p = p.flatten()
    return -sum(pi*np.log2(pi) for pi in p if pi)

def conditional_shannon_entropy(p, *conditional_indices):
    """Shannon entropy of P(X) conditional on variable j."""

    axis = tuple(i for i in np.arange(len(p.shape)) if i not in conditional_indices)

    return shannon_entropy(p) - shannon_entropy(np.sum(p, axis=axis))

def mutual_information(prob, j):
    """Mutual information between variables X and variable j."""
    return shannon_entropy(np.sum(prob, axis=j)) - conditional_shannon_entropy(prob, j)

def conditional_mutual_information(p, j, *conditional_indices):
    """Mutual information between variables X and variable j conditional on variable k."""
    return conditional_shannon_entropy(np.sum(p, axis=j), *conditional_indices) - conditional_shannon_entropy(p, j, *conditional_indices)

# Rank the MI between survival and every other variable
scores = {}
features = list(set(dataset.columns).difference(('survived',)))
for feature in features:
    scores[feature] = mutual_information(prob(dataset[['survived', feature]].values), 0)

labels, values = zip(*sorted(scores.items(), key=lambda pair: pair[1], reverse=True))

# Plot the MI between survival and every other variable
plt.figure()
ax1 = plt.subplot(1, 2, 1)
ax1.set_ylabel('MI Between Survival and Feature')
ax1.set_title("Mutual Information")
plt.bar(np.arange(len(labels)), values)
plt.xticks(np.arange(len(labels)), labels, rotation=90)

# Build a QUBO that maximizes MI between survival and a subset of features
bqm = dimod.BinaryQuadraticModel.empty(dimod.BINARY)

# Add biases as (negative) MI with survival for each feature
for feature in features:
    mi = mutual_information(prob(dataset[['survived', feature]].values), 1)
    bqm.add_variable(feature, -mi)

# Add interactions as (negative) MI with survival for each set of 2 features
for f0, f1 in itertools.combinations(features, 2):
    mi = conditional_mutual_information(prob(dataset[['survived', f0, f1]].values), 1, 2)
    bqm.add_interaction(f0, f1, -mi)

bqm.normalize()  # Normalize biases & interactions to the range -1, 1


# Set up a QPU sampler with a fully-connected graph of all the variables
qpu_sampler = DWaveSampler(solver={'qpu': True})

embedding = find_clique_embedding(bqm.variables,
                                  16, 16, 4,  # size of the chimera lattice
                                  target_edges=qpu_sampler.edgelist)

sampler = FixedEmbeddingComposite(qpu_sampler, embedding)

# For each value for k, penalize selection of fewer or more features
selected_features = np.zeros((len(features), len(features)))
for k in range(1, len(features) + 1):
    kbqm = bqm.copy()
    kbqm.update(dimod.generators.combinations(features, k, strength=6))

    # sample = sampler.sample(kbqm, num_reads=10000).first.sample
    sample = dimod.ExactSolver().sample(kbqm).first.sample

    for fi, f in enumerate(features):
        selected_features[k-1, fi] = sample[f]

# Plot the best feature set for each value of k
# plt.subplot(1, 2, 2)
# plt.imshow(selected_features)
# plt.ylabel('number of features')
# plt.xticks(np.arange(len(features)), features, rotation=90)
#
# plt.show()
ax2 = plt.subplot(1, 2, 2)
ax2.set_title("Best Feature Selection")
ax2.imshow(selected_features, cmap=colors.ListedColormap(['white', 'red']))
ax2.set_yticks(np.arange(-0.5, len(features)), minor=True)
ax2.set_yticks(np.arange(len(features)))
ax2.set_yticklabels(np.arange(1, len(features)+1))
ax2.set_ylabel('Number of Selected Features')
ax2.set_xticks(np.arange(-0.5, len(features)), minor=True)
ax2.set_xticks(np.arange(len(features)))
ax2.set_xticklabels(features, rotation=90)
ax2.grid(which='minor', color='black')
plt.tight_layout()
plt.show()
