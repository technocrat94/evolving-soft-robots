"""Ablation invariants and independently checkable exact statistical cases."""
import unittest
import numpy as np
import config as C
from evolve import random_genome,next_generation
from experiments import paired_sign_flip,holm_adjust
from sim import is_valid


class ExperimentTests(unittest.TestCase):
    def test_frozen_genes_survive_multiple_generations(self):
        for condition in C.EXPERIMENT_CONDITIONS:
            rng=np.random.default_rng(99)
            population=[random_genome(rng,condition) for _ in range(8)]
            for _ in range(4):
                for genome in population:
                    self.assertTrue(is_valid(genome.body))
                    if condition=='body_only':
                        self.assertEqual(genome.omega,3.0)
                        np.testing.assert_array_equal(genome.phases,np.zeros(genome.body.shape))
                    if condition=='control_only':
                        np.testing.assert_array_equal(genome.body,np.array(C.DEMO_BODY))
                population=next_generation(population,np.arange(8,dtype=float),rng,condition)

    def test_exact_statistics(self):
        self.assertEqual(paired_sign_flip(np.arange(1,6),np.zeros(5))['p_value'],2/32)
        self.assertEqual(paired_sign_flip(np.zeros(5),np.zeros(5))['p_value'],1)
        result=paired_sign_flip([1,-1],[0,0])
        self.assertEqual(result['p_value'],1)
        self.assertEqual(result['permutations'],4)
        self.assertEqual(paired_sign_flip([1,2,3],[0,0,0])['p_value'],0.25)
        self.assertEqual(paired_sign_flip([0,0,0],[1,2,3])['p_value'],0.25)
        with self.assertRaises(ValueError):
            paired_sign_flip([1],[1,2])

    def test_holm_correction(self):
        np.testing.assert_allclose(holm_adjust([0.03,0.01]),[0.03,0.02])
        np.testing.assert_allclose(holm_adjust([0.0625,0.0625]),[0.125,0.125])


if __name__=='__main__':
    unittest.main()
