"""Targeted mesh, validity, determinism, contact and stability checks."""
import unittest
import numpy as np
import config as C
from sim import build_robot, is_valid, simulate


class PhysicsTests(unittest.TestCase):
    def test_shared_edges(self):
        p, springs, _, lengths = build_robot(np.array([[3, 4]]))
        self.assertEqual(len(p), 6)
        self.assertEqual(len(springs), 11)
        self.assertEqual(len(set(map(tuple, springs))), 11)
        self.assertTrue(np.all(lengths > 0))

    def test_validity(self):
        for body in ([[0]], [[1]], [[3,0],[0,4]], [[5]], [[3.0]]):
            self.assertFalse(is_valid(np.array(body)))
            self.assertEqual(simulate(np.array(body)), 0.0)
        self.assertTrue(is_valid(np.array([[3,1],[0,4]])))

    def test_recording_and_determinism(self):
        body = np.array(C.DEMO_BODY)
        params = {'omega': C.OMEGA, 'phases': np.array(C.DEMO_PHASES)}
        distance, frames = simulate(body, params, record=True)
        self.assertEqual(distance, simulate(body, params))
        self.assertTrue(np.all(np.isfinite(frames)))
        self.assertGreaterEqual(frames[:,:,1].min(), 0)
        self.assertLess(frames[:,:,1].max(), 6)
        self.assertGreater(distance, 0)

    def test_ground_contact_occupancy(self):
        trace = {}
        simulate(np.array(C.DEMO_BODY),
                 {'omega': C.OMEGA, 'phases': np.array(C.DEMO_PHASES)},
                 diagnostics=trace)
        self.assertEqual(len(trace['min_y']), round(C.SIM_SECONDS/C.DT)+1)
        self.assertGreater(np.mean(trace['min_y'][1:] <= C.CONTACT_TOLERANCE), 0.85)
        self.assertLess(trace['min_y'].max(), 0.2)

    def test_dense_stability(self):
        for material in (3, 4):
            _, frames = simulate(np.full((5,5), material), record=True)
            self.assertGreater(len(frames), 0)
            self.assertTrue(np.all(np.isfinite(frames)))
            self.assertGreaterEqual(frames[:,:,1].min(), 0)


if __name__ == '__main__':
    unittest.main()
