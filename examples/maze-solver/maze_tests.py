# Copyright 2019 D-Wave Systems Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import itertools
import re
import unittest

from dimod import BinaryQuadraticModel
from maze import Maze, get_label, get_maze_bqm
from neal import SimulatedAnnealingSampler


def fill_with_zeros(solution_dict, n_rows, n_cols, ignore_list=None):
    keys = set(itertools.chain(solution_dict.keys(), ignore_list or []))

    # Setting west direction to zero
    for i in range(n_rows):
        for j in range(n_cols + 1):
            west = get_label(i, j, 'w')

            if west not in keys:
                solution_dict[west] = 0

    # Setting north direction to zero
    for i in range(n_rows + 1):
        for j in range(n_cols):
            north = get_label(i, j, 'n')

            if north not in keys:
                solution_dict[north] = 0


def get_energy(solution_dict, bqm):
    min_energy = float('inf')
    aux_variables = [v for v in bqm.variables if re.match(r'aux\d+$', v)]

    # Try all possible values of auxiliary variables
    for aux_values in itertools.product([0, 1], repeat=len(aux_variables)):
        for variable, value in zip(aux_variables, aux_values):
            solution_dict[variable] = value

        temp_energy = bqm.energy(solution_dict)

        if temp_energy < min_energy:
            min_energy = temp_energy

    return min_energy


class TestMazeSolverConstraints(unittest.TestCase):
    def test_valid_move_constraint(self):
        n_rows = 2
        n_cols = 3
        start = '0,1n'
        end = '0,3w'
        maze = Maze(n_rows, n_cols, start, end, ['1,2n', '1,2w'])
        maze._apply_valid_move_constraint()

        # No path at all, not even at start or end locations
        no_path_solution = {}
        fill_with_zeros(no_path_solution, n_rows, n_cols)
        self.assertTrue(maze.csp.check(no_path_solution))

        # Broken path
        broken_path_solution = {'1,0n': 1, '1,1w': 1}
        fill_with_zeros(broken_path_solution, n_rows, n_cols)
        self.assertFalse(maze.csp.check(broken_path_solution))

        # Revisiting a tile 0,1
        revisit_tile_solution = {'0,1w': 1, '1,0n': 1, '1,1w': 1, '1,1n': 1, '0,2w': 1, start: 1, end: 1}
        fill_with_zeros(revisit_tile_solution, n_rows, n_cols)
        self.assertFalse(maze.csp.check(revisit_tile_solution))

        # Good path
        good_path_solution = {'0,2w': 1, start: 1, end: 1}
        fill_with_zeros(good_path_solution, n_rows, n_cols)
        self.assertTrue(good_path_solution)

    def test_set_start_and_end(self):
        # Create maze
        n_rows = 5
        n_cols = 3
        start = '4,3w'
        end = '0,2n'
        maze = Maze(n_rows, n_cols, start, end, [])
        maze._apply_valid_move_constraint()  # Apply constraint to populate csp variables

        # Check to see that start and end are in csp.variables
        self.assertTrue(start in maze.csp.variables)
        self.assertTrue(end in maze.csp.variables)

        # Check to see that start and end have been fixed
        maze._set_start_and_end()
        self.assertFalse(start in maze.csp.variables)
        self.assertFalse(end in maze.csp.variables)

        # Check that start and end are fixed to 1.
        # If start and end were fixed to 0, valid_move_constraint would be satisfied with the no_path_solution.
        no_path_solution = {}
        fill_with_zeros(no_path_solution, n_rows, n_cols, [start, end])
        self.assertFalse(maze.csp.check(no_path_solution))

    def test_borders_constraint(self):
        # Create maze
        n_rows = 3
        n_cols = 3
        start = '0,1n'
        end = '0,3w'
        maze = Maze(n_rows, n_cols, start, end, ['1,1w', '2,1n'])
        maze._apply_valid_move_constraint()  # Apply constraint to populate csp variables
        maze._set_start_and_end()  # Start and end locations should not be considered as borders

        # Grab border variables
        borders = {get_label(i, 0, 'w') for i in range(n_rows)}  # West border
        borders.update({get_label(i, n_cols, 'w') for i in range(n_rows)})  # East border
        borders.update({get_label(0, j, 'n') for j in range(n_cols)})  # North border
        borders.update({get_label(n_rows, j, 'n') for j in range(n_cols)})  # South border
        borders.remove(start)
        borders.remove(end)

        # Check to see that border appears as a variable in maze.csp
        for border in borders:
            self.assertTrue(border in maze.csp.variables)

        # Fix borders
        maze._set_borders()

        # Check to see that borders are fixed; they would no longer appear as variables
        for border in borders:
            self.assertFalse(border in maze.csp.variables)

        # Verify that borders are fixed to 0.
        # If borders were fixed to 1, this good_path_solution would cause the valid_move_constraint to fail.
        good_path_solution = {'0,2w': 1}
        fill_with_zeros(good_path_solution, n_rows, n_cols, [start, end])
        self.assertTrue(maze.csp.check(good_path_solution))

    def test_inner_walls(self):
        # Create maze
        n_rows = 4
        n_cols = 7
        start = '2,0w'
        end = '0,3n'
        walls = ['2,3w', '2,4w', '2,5w']
        maze = Maze(n_rows, n_cols, start, end, walls)
        maze._apply_valid_move_constraint()  # Apply constraint to populate csp variables

        # Check to see that walls appear as variables in maze.csp
        for wall in walls:
            self.assertTrue(wall in maze.csp.variables)

        # Fix wall values
        maze._set_inner_walls()

        # Check to see that walls are fixed; they would no longer appear as variables
        for wall in walls:
            self.assertFalse(wall in maze.csp.variables)

        # Verify that walls are fixed to 0
        # circle_solution surrounds the inner walls, if walls are fixed to 1, solution will fail valid_move_constraint.
        # Since start and end locations have not been fixed, a circle is valid path
        circle_solution = {'2,2n': 1, '3,2n': 1, '3,3w': 1, '3,4w': 1, '3,5w': 1, '3,5n': 1, '2,5n': 1, '1,5w': 1,
                           '1,4w': 1, '1,3w': 1}
        fill_with_zeros(circle_solution, n_rows, n_cols)  # No ignore_list because we didn't fix start and end
        self.assertTrue(maze.csp.check(circle_solution))


class TestMazeSolverResponse(unittest.TestCase):
    def compare(self, sample, expected):
        """Comparing response to expected results
        """
        # Comparing variables found in sample and expected
        expected_keys = set(expected.keys())
        sample_keys = set(sample.keys())
        common_keys = expected_keys & sample_keys
        different_keys = expected_keys - sample_keys  # expected_keys is a superset

        # Check that common variables match
        for key in common_keys:
            if re.match(r'aux\d+$', key):
                continue
            self.assertEqual(sample[key], expected[key], "Key {} does not match with expected value".format(key))

        # Check that non-existent 'sample' variables are 0
        for key in different_keys:
            if re.match(r'aux\d+$', key):
                continue
            self.assertEqual(expected[key], 0, "Key {} does not match with expected value".format(key))

    def test_energy_level_one_optimal_path(self):
        # Create maze
        n_rows = 2
        n_cols = 4
        start = '1,4w'
        end = '2,2n'
        walls = []
        maze = Maze(n_rows, n_cols, start, end, walls)
        bqm = maze.get_bqm()

        # Grab energy levels of different paths
        shortest_path = {'1,3w': 1}
        longer_path0 = {'1,2n': 1, '0,3w': 1, '1,3n': 1}
        longer_path1 = {'1,2w': 1, '1,1n': 1, '0,2w': 1, '0,3w': 1, '1,3n': 1}
        no_path = {}

        fill_with_zeros(shortest_path, n_rows, n_cols, [start, end])
        fill_with_zeros(longer_path0, n_rows, n_cols, [start, end])
        fill_with_zeros(longer_path1, n_rows, n_cols, [start, end])
        fill_with_zeros(no_path, n_rows, n_cols, [start, end])

        energy_shortest_path = get_energy(shortest_path, bqm)
        energy_longer_path0 = get_energy(longer_path0, bqm)
        energy_longer_path1 = get_energy(longer_path1, bqm)
        energy_no_path = get_energy(no_path, bqm)

        # Compare energy levels
        self.assertLess(energy_shortest_path, energy_longer_path0)
        self.assertLess(energy_shortest_path, energy_longer_path1)
        self.assertLess(energy_longer_path0, energy_longer_path1)
        self.assertLess(energy_shortest_path, energy_no_path)

    def test_energy_level_multiple_optimal_paths(self):
        # Create maze
        n_rows = 3
        n_cols = 4
        start = '0,0w'
        end = '1,4w'
        walls = ['1,1w']
        maze = Maze(n_rows, n_cols, start, end, walls)
        bqm = maze.get_bqm()

        # Shortest paths through maze; should share same energy level
        shortest_path0 = {'0,1w': 1, '1,1n': 1, '1,2w': 1, '1,3w': 1}
        shortest_path1 = {'0,1w': 1, '0,2w': 1, '1,2n': 1, '1,3w': 1}
        shortest_path2 = {'0,1w': 1, '0,2w': 1, '0,3w': 1, '1,3n': 1}

        fill_with_zeros(shortest_path0, n_rows, n_cols, [start, end])
        fill_with_zeros(shortest_path1, n_rows, n_cols, [start, end])
        fill_with_zeros(shortest_path2, n_rows, n_cols, [start, end])

        energy_shortest_path0 = get_energy(shortest_path0, bqm)
        energy_shortest_path1 = get_energy(shortest_path1, bqm)
        energy_shortest_path2 = get_energy(shortest_path2, bqm)

        self.assertEqual(energy_shortest_path0, energy_shortest_path1)
        self.assertEqual(energy_shortest_path0, energy_shortest_path2)

        # Compare energy level of longer path with shortest path
        longer_path = {'0,1w': 1, '1,1n': 1, '2,1n': 1, '2,2w': 1, '2,2n': 1, '1,3w': 1}
        fill_with_zeros(longer_path, n_rows, n_cols, [start, end])
        energy_longer_path = get_energy(longer_path, bqm)

        self.assertGreater(energy_longer_path, energy_shortest_path0)

        # Compare energy level of no path with shortest path
        no_path = {}
        fill_with_zeros(no_path, n_rows, n_cols, [start, end])
        energy_no_path = get_energy(no_path, bqm)

        self.assertGreater(energy_no_path, energy_shortest_path0)

    def test_maze_heuristic_response(self):
        """Small and simple maze to verify that it is possible get a solution.
        """
        # Create maze
        n_rows = 3
        n_cols = 3
        start = '0,0n'
        end = '3,2n'
        walls = ['1,0n', '2,1n', '2,2n']
        maze = Maze(n_rows, n_cols, start, end, walls)
        bqm = maze.get_bqm()

        # Sample and test that a response is given
        sampler = SimulatedAnnealingSampler()
        response = sampler.sample(bqm, num_reads=1000)
        response_sample = next(response.samples())
        self.assertGreaterEqual(len(response), 1)

        # Test heuristic response
        expected_solution = {'0,1w': 1, '1,1n': 1, '1,1w': 1, '2,0n': 1, '2,1w': 1, '2,2w': 1}
        fill_with_zeros(expected_solution, n_rows, n_cols, [start, end])
        self.compare(response_sample, expected_solution)


class TestGetMazeBqm(unittest.TestCase):
    def test_bqm_return(self):
        """get_maze_bqm(..) is merely a wrapper. This test is to ensure that the wrapper works.
        """
        # Create maze
        n_rows = 2
        n_cols = 2
        start = '0,0n'
        end = '1,0w'
        walls = ['1,1n']

        # Get bqm
        bqm = get_maze_bqm(n_rows, n_cols, start, end, walls)
        self.assertIsInstance(bqm, BinaryQuadraticModel)


if __name__ == "__main__":
    unittest.main()
