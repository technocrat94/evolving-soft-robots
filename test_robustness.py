import unittest
import numpy as np

import config as C
from controllers import ROUGH_X, ROUGH_Y, ground, neural_output, sensors
from robustness import crossover, mutate, random_controller
from sim import _mesh, simulate


class FeedbackControlTests(unittest.TestCase):
    def setUp(self):
        self.body=np.array(C.DEMO_BODY,dtype=int)

    def test_neural_controller_shape_bounds_and_simulation(self):
        controller=random_controller('closed_loop',self.body,np.random.default_rng(3))
        output=neural_output(controller.parameters(),np.linspace(-1,1,C.NN_INPUTS))
        self.assertEqual(output.shape,(np.count_nonzero((self.body==3)|(self.body==4)),))
        self.assertTrue(np.all(np.abs(output)<=1))
        diagnostics={}
        value=simulate(self.body,controller.parameters(),steps=80,diagnostics=diagnostics)
        self.assertTrue(np.isfinite(value));self.assertTrue(diagnostics['stable'])

    def test_sensor_order_and_contact_flags(self):
        points,_,_,_,_=_mesh(self.body);points[:,1]+=C.START_HEIGHT
        reference=points-points.mean(axis=0);velocities=np.zeros_like(points)
        front=reference[:,0]>=0
        values,tilt=sensors(reference,points,velocities,0.0,front,0.0,0.0,3.0)
        self.assertEqual(values.shape,(7,));self.assertAlmostEqual(tilt,0)
        self.assertEqual(tuple(values[3:5]),(False,False))
        self.assertEqual(tuple(values[5:]),(0.0,1.0))

    def test_rough_ground_is_reproducible_and_enforced(self):
        heights,slopes=ground(ROUGH_X,'rough')
        np.testing.assert_allclose(heights,ROUGH_Y)
        self.assertTrue(np.all(np.isfinite(slopes)))
        controller=random_controller('open_loop',self.body,np.random.default_rng(4))
        diagnostics={};simulate(self.body,controller.parameters(),steps=500,
                                terrain='rough',diagnostics=diagnostics)
        self.assertGreaterEqual(diagnostics['min_y'].min(),-1e-10)

    def test_variation_preserves_parent_and_omega_bounds(self):
        rng=np.random.default_rng(5)
        first=random_controller('closed_loop',self.body,rng)
        second=random_controller('closed_loop',self.body,rng)
        snapshot=first.w1.copy()
        child=mutate(crossover(first,second,rng),rng)
        np.testing.assert_array_equal(first.w1,snapshot)
        self.assertGreaterEqual(child.omega,C.OMEGA_MIN)
        self.assertLessEqual(child.omega,C.OMEGA_MAX)

    def test_push_is_backward_and_deterministic(self):
        controller=random_controller('open_loop',self.body,np.random.default_rng(6))
        steps=round((C.PUSH_TIME+.1)/C.DT)
        no_push=simulate(self.body,controller.parameters(),steps=steps)
        pushed=simulate(self.body,controller.parameters(),steps=steps,push=True)
        repeated=simulate(self.body,controller.parameters(),steps=steps,push=True)
        self.assertEqual(pushed,repeated)
        self.assertLess(pushed,no_push)


if __name__=='__main__':
    unittest.main()
