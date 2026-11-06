"""Checks for genome integrity, bounded control, elitism and toppling detection."""
import tempfile
import unittest
from pathlib import Path
import numpy as np
import config as C
from evolve import random_genome, mutate, next_generation, evaluate, save_genome, load_genome, audit_genome
from sim import is_valid, upright_cosine, simulate


class EvolutionTests(unittest.TestCase):
    def test_initialization_reproducible(self):
        left, right = np.random.default_rng(42), np.random.default_rng(42)
        for _ in range(20):
            a, b = random_genome(left), random_genome(right)
            self.assertTrue(is_valid(a.body))
            np.testing.assert_array_equal(a.body, b.body)
            np.testing.assert_array_equal(a.phases, b.phases)
            self.assertEqual(a.omega, b.omega)

    def test_mutation_clamps_preserves_parent(self):
        rng = np.random.default_rng(2)
        parent = random_genome(rng)
        original = parent.copy()
        for bound in (C.OMEGA_MIN, C.OMEGA_MAX):
            parent.omega = bound
            for _ in range(100):
                child = mutate(parent, rng)
                self.assertGreaterEqual(child.omega, C.OMEGA_MIN)
                self.assertLessEqual(child.omega, C.OMEGA_MAX)
        np.testing.assert_array_equal(parent.body, original.body)
        np.testing.assert_array_equal(parent.phases, original.phases)

    def test_elites_unchanged_children_valid(self):
        rng = np.random.default_rng(4)
        population = [random_genome(rng) for _ in range(10)]
        snapshots = [g.copy() for g in population]
        children = next_generation(population, np.arange(10, dtype=float), rng)
        self.assertEqual(len(children), 10)
        for index, parent_index in enumerate((9, 8)):
            np.testing.assert_array_equal(children[index].body, population[parent_index].body)
            np.testing.assert_array_equal(children[index].phases, population[parent_index].phases)
            self.assertEqual(children[index].omega, population[parent_index].omega)
            self.assertFalse(np.shares_memory(children[index].body, population[parent_index].body))
        for parent, old in zip(population, snapshots):
            np.testing.assert_array_equal(parent.body, old.body)
        self.assertTrue(all(is_valid(child.body) for child in children))

    def test_posture_ignores_translation_detects_rotation(self):
        reference = np.array([[-1.,-2.], [1.,-2.], [1.,2.], [-1.,2.]])
        for degrees in (0, 30, 60, 90, 180):
            theta = np.deg2rad(degrees)
            rotation = np.array([[np.cos(theta),-np.sin(theta)],
                                 [np.sin(theta),np.cos(theta)]])
            moved = reference @ rotation.T + np.array([150., 4.])
            self.assertAlmostEqual(upright_cosine(reference, moved), np.cos(theta))

    def test_positive_distance_from_falling_is_disqualified(self):
        # Reproducible asymmetric, tall body that topples; mirror it so the
        # passive fall is rightward. Raw displacement must not earn fitness.
        rng = np.random.default_rng(42)
        random_genome(rng)
        genome = random_genome(rng)
        genome.body = np.fliplr(genome.body).copy()
        genome.phases = np.fliplr(genome.phases).copy()
        result = evaluate(genome)
        self.assertTrue(result[2])
        self.assertGreater(result[1], 0.5)
        self.assertEqual(result[0], 0.0)

    def test_passive_audit_preserves_configuration(self):
        genome = random_genome(np.random.default_rng(9))
        amplitude = C.AMPLITUDE
        audit = audit_genome(genome)
        self.assertEqual(C.AMPLITUDE, amplitude)
        self.assertEqual(audit['distance_m'], evaluate(genome)[1])
        try:
            C.AMPLITUDE = 0.0
            trace = {}
            simulate(genome.body, genome.controller(), diagnostics=trace)
        finally:
            C.AMPLITUDE = amplitude
        self.assertEqual(audit['actuation_disabled_distance_m'], trace['raw_distance'])
        self.assertGreaterEqual(audit['grounded_percentage'], 0)
        self.assertLessEqual(audit['grounded_percentage'], 100)

    def test_save_load_and_simulator_clamp(self):
        genome = random_genome(np.random.default_rng(9))
        params = genome.controller()
        params['omega'] = 99.0
        high = simulate(genome.body, params, steps=100)
        params['omega'] = C.OMEGA_MAX
        self.assertEqual(high, simulate(genome.body, params, steps=100))
        result = evaluate(genome)
        with tempfile.TemporaryDirectory() as folder:
            filename = Path(folder)/'robot.npz'
            save_genome(filename, genome, result[0], result)
            loaded = load_genome(filename)
            np.testing.assert_array_equal(loaded.body, genome.body)
            np.testing.assert_array_equal(loaded.phases, genome.phases)
            self.assertEqual(loaded.omega, genome.omega)
            self.assertEqual(evaluate(loaded), result)


if __name__ == '__main__':
    unittest.main()
