import os
import subprocess
import unittest

# /path/to/demos/maximum-cut/tests/test_maximum_cut.py
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestDemo(unittest.TestCase):
    def test_smoke(self):
        """run maximum_cut.py and check that nothing crashes"""

        demo_file = os.path.join(project_dir, 'maximum_cut.py')
        subprocess.check_output(["python", demo_file])