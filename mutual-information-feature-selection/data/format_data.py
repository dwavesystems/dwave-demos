# reformat the data
import os
import re

import numpy as np
import pandas as pd

# make this runnable from other locations
my_loc = os.path.dirname(os.path.abspath(__file__))
os.chdir(my_loc)


dataset = pd.read_csv('titanic.csv')


# statistics about name

def get_title(name):
    title_search = re.search(r" ([A-Za-z]+)\.", name)
    # If the title exists, extract and return it.
    if title_search:

        title = title_search.group(1)

        # do some grouping
        if title in ('Miss', 'Ms', 'Mlle'):
            return 'miss'
        if title in ('Mrs', 'Mme'):
            return 'mrs'
        if title in ['Lady', 'Countess', 'Capt', 'Col', 'Don', 'Dr', 'Major',
                     'Rev', 'Sir', 'Jonkheer', 'Dona']:
            return 'rare'

        return title.lower()
    return ""


dataset['title'] = dataset['name'].apply(get_title)

for title in dataset['title'].unique():
    dataset[title] = dataset['title'].apply(lambda t: t == title)

# alone or not
dataset['alone'] = (dataset["sibsp"] + dataset["parch"]).apply(lambda x: x == 0)

# in a cabin or not
dataset['cabin'] = dataset['cabin'].apply(lambda c: not pd.isna(c))

# sex to binary
dataset['sex'] = dataset['sex'].apply(lambda s: s == 'female')*1

# embarked port
dataset['embarked port S'] = dataset['embarked'].apply(lambda x: x == 'S')
dataset['embarked port C'] = dataset['embarked'].apply(lambda x: x == 'C')
dataset['embarked port Q'] = dataset['embarked'].apply(lambda x: x == 'Q')

# drop the folks with no age or fare
dataset = dataset[np.isfinite(dataset['age'])]
dataset = dataset[np.isfinite(dataset['fare'])]

# make age discrete by grouping into 20s (rounding down)
dataset['age'] = dataset['age'].apply(lambda a: 2*int(a // 20))

# make fare discrete by rounding down to the $100
dataset['fare'] = dataset['fare'].apply(lambda f: int(f // 100))

# clean out old columns
dataset.drop(['name', 'sibsp', 'parch', 'ticket', 'embarked',
              'boat', 'body', 'home.dest', 'title'],
             axis=1, inplace=True)

# finally write
dataset.to_csv('formatted_titanic.csv', index=False)

# print(dataset)
