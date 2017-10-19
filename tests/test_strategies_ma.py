# -*- coding: utf-8 -*-
import unittest
import pandas as pd
import numpy as np
import backtradercn.strategies.ma as bsm


class MATrendStrategyTestCase(unittest.TestCase):
    def test_run(self):
        self._test_get_params_list()

    def _test_get_params_list(self):
        training_data = pd.DataFrame(np.random.rand(10, 2))
        params_list = bsm.MATrendStrategy.get_params_list(training_data)

        self.assertEqual(len(params_list), 4)
