from unittest import TestCase

import pandas as pd
import pytest

from analytics.strategies.sma_crossovers import SMAStrategy


class TestSMAStrategy(TestCase):
    def setUp(self) -> None:

        self.sample_data = pd.read_csv("./mock_data/sample_data.csv")

        # definehappy_path variables
        self.slow_ma = 20
        self.fast_ma = 10

        self.sma_obj = SMAStrategy(
            scrip_df=self.sample_data, slow_ma=self.slow_ma, fast_ma=self.fast_ma
        )

    def test_smacrossovers__happy_path(self):

        # evaluate sma cross over stratgy

        sma_df = self.sma_obj.sma_sessions()

        column_suffix = f"{self.slow_ma}_{self.fast_ma}"
        expected_columns = [
            f"{col}_{column_suffix}"
            for col in [
                "sma_signal",
                "sma_signal",
                "label",
            ]
        ]

        self.assertTrue(set(expected_columns).issubset(sma_df.columns))

    def test_smacrossovers__fails_validation(self):

        with self.assertRaises(AssertionError):
            # slow_ma must always be greater than fast_ma
            SMAStrategy(
                scrip_df=self.sample_data, slow_ma=self.fast_ma, fast_ma=self.slow_ma
            )
