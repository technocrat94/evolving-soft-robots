import unittest
import numpy as np
import config as C
from controllers import ground,neural_output
from domain_randomization import training_schedule,heldout_schedule,evaluate_batch
from robustness import random_controller,mutate,crossover
from sim import simulate


class DomainRandomizationTests(unittest.TestCase):
    def setUp(self):self.body=np.array(C.DEMO_BODY)

    def test_environment_schedule_shared_reproducible_and_disjoint(self):
        schedule=training_schedule(42)
        self.assertEqual(schedule,training_schedule(42))
        self.assertNotEqual(schedule[0],schedule[1])
        training={e['terrain_seed'] for batch in schedule for e in batch if 'terrain_seed' in e}
        test={e['terrain_seed'] for e in heldout_schedule() if 'terrain_seed' in e}
        self.assertFalse(training & test);self.assertEqual(len(training),80)
        self.assertEqual(len(heldout_schedule()),21)
        for batch in schedule:
            self.assertEqual(len(batch),4)
            self.assertTrue(1.5<=batch[3]['push_time']<=3.5)
            self.assertTrue(.8<=batch[3]['push_magnitude']<=2)

    def test_clock_only_masks_sensors_with_identical_architecture(self):
        rng=np.random.default_rng(42);clock=random_controller('neural_clock_only',self.body,rng)
        feedback=random_controller('closed_loop',self.body,np.random.default_rng(42))
        np.testing.assert_array_equal(clock.w1,feedback.w1)
        first=np.array([1,2,3,1,1,.4,.8]);second=first.copy();second[:5]=0
        np.testing.assert_array_equal(neural_output(clock.parameters(),first),neural_output(clock.parameters(),second))
        self.assertFalse(np.array_equal(neural_output(feedback.parameters(),first),neural_output(feedback.parameters(),second)))
        child=mutate(crossover(clock,clock,rng),rng)
        self.assertEqual(child.kind,'neural_clock_only')

    def test_seeded_terrain_and_push_arguments(self):
        x=np.linspace(0,4,100)
        self.assertFalse(np.array_equal(ground(x,'rough',100001)[0],ground(x,'rough',2000000)[0]))
        diag={};simulate(self.body,steps=200,terrain='rough',terrain_seed=2000000,diagnostics=diag)
        self.assertGreaterEqual(diag['min_y'].min(),-1e-10)
        unpushed=simulate(self.body,steps=100)
        pushed=simulate(self.body,steps=100,push=True,push_time=.1,push_magnitude=1.2)
        self.assertLess(pushed,unpushed)

    def test_clock_mask_applies_to_complete_rollout(self):
        clock=random_controller('neural_clock_only',self.body,np.random.default_rng(43))
        feedback=clock.copy();feedback.kind='closed_loop';feedback.w1[:,:5]=0
        _,clock_frames=simulate(self.body,clock.parameters(),steps=100,record=True)
        _,feedback_frames=simulate(self.body,feedback.parameters(),steps=100,record=True)
        np.testing.assert_allclose(clock_frames,feedback_frames,atol=1e-12,rtol=1e-12)

    def test_four_episode_mean_includes_zero_for_falls(self):
        genome=random_controller('open_loop',self.body,np.random.default_rng(42))
        episodes=training_schedule(42,1)[0]
        rows=evaluate_batch((self.body,genome,episodes))
        self.assertEqual(len(rows),4)
        for fitness,fell,stable,raw in rows:
            self.assertEqual(fitness,0 if fell else raw);self.assertTrue(stable)


if __name__=='__main__':unittest.main()
