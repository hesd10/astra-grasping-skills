"""Synthetic offline cases only. Never imports a motor or camera driver."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill.safety import (require_fresh_evidence, require_preload_window,
                          require_verified_lift, require_lift_evidence)


class EvidenceTests(unittest.TestCase):
    def fresh(self, **updates):
        values = dict(observed_at=10., now=10.2, maximum_age=.5, invalidated_at=9.)
        values.update(updates)
        require_fresh_evidence(**values)

    def test_current_and_no_invalidation(self):
        self.fresh()
        self.fresh(invalidated_at=None)

    def test_cached_pre_event_observation_cannot_authorize(self):
        for updates in (dict(observed_at=9.), dict(invalidated_at=10.), dict(now=11.)):
            with self.subTest(updates=updates), self.assertRaises(RuntimeError):
                self.fresh(**updates)

    def test_invalid_timing(self):
        for updates in (dict(observed_at=-1.), dict(now=9.), dict(maximum_age=0.),
                        dict(invalidated_at=11.), dict(invalidated_at=-1.)):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                self.fresh(**updates)
        for key in ('observed_at', 'now', 'maximum_age', 'invalidated_at'):
            for invalid in (math.nan, math.inf, -math.inf):
                with self.subTest(key=key, invalid=invalid), self.assertRaises(ValueError):
                    self.fresh(**{key: invalid})


class PreloadTests(unittest.TestCase):
    def window(self, samples=None, **updates):
        values = dict(now=12.1, maximum_age=.5, minimum_duration=2., maximum_gap=1.2,
                      baseline_preload=10., minimum_preload=4., maximum_fractional_loss=.2,
                      invalidated_at=9.)
        values.update(updates)
        require_preload_window([(10., 10.), (11., 9.), (12., 9.)]
                               if samples is None else samples, **values)

    def test_valid_window(self):
        self.window()
        self.window(invalidated_at=None)

    def test_mid_window_drop_is_not_hidden_by_recovery(self):
        for middle in (7., 3., -9.):
            with self.subTest(middle=middle), self.assertRaises(RuntimeError):
                self.window([(10., 10.), (11., middle), (12., 10.)])

    def test_absolute_minimum_independent_of_relative_loss(self):
        with self.assertRaises(RuntimeError):
            self.window(minimum_preload=9.5, maximum_fractional_loss=.8)

    def test_must_rebuild_after_invalidating_event(self):
        with self.assertRaises(RuntimeError):
            self.window(invalidated_at=10.5)

    def test_missing_delayed_short_and_stopped_streams(self):
        for samples, updates in (
            ([(10., 10.), (12., 10.)], {}),
            (None, dict(now=12.7)),
            (None, dict(now=13.3, maximum_age=2.)),
            (None, dict(minimum_duration=3.)),
        ):
            with self.subTest(samples=samples, updates=updates), self.assertRaises(RuntimeError):
                self.window(samples, **updates)

    def test_single_duplicate_reversed_future_and_nonfinite_samples(self):
        cases = ([], [(12., 10.)], [(10., 10.), (10., 10.), (12., 10.)],
                 [(11., 10.), (10., 10.), (12., 10.)],
                 [(10., 10.), (11., 10.), (12., math.nan)],
                 [(10., 10.), (math.inf, 10.)], [(-1., 10.), (0., 10.)])
        for samples in cases:
            with self.subTest(samples=samples), self.assertRaises(ValueError):
                self.window(samples)
        with self.assertRaises(ValueError):
            self.window(now=11.9)

    def test_invalid_bounds(self):
        for key in ('minimum_duration', 'maximum_gap', 'baseline_preload', 'minimum_preload'):
            for invalid in (0., -1., math.nan, math.inf):
                with self.subTest(key=key, invalid=invalid), self.assertRaises(ValueError):
                    self.window(**{key: invalid})
        for invalid in (-.1, 1., math.nan, math.inf):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                self.window(maximum_fractional_loss=invalid)

    def test_owner_inhibits_new_commands_and_latches_failure(self):
        # A mock demonstrates the required caller contract, not a physical controller.
        # No recorded goals or device roles are used; these objects are sentinels.
        active_support = object()
        owner = dict(active_support=active_support, latched=False, forwarded=[])

        def request_extension(samples):
            if owner['latched']:
                return
            try:
                self.window(samples)
            except (RuntimeError, ValueError):
                owner['latched'] = True
                return
            owner['forwarded'].append('synthetic extension')

        request_extension([(10., 10.), (11., 7.), (12., 10.)])
        request_extension([(10., 10.), (11., 10.), (12., 10.)])
        self.assertTrue(owner['latched'])
        self.assertEqual(owner['forwarded'], [])
        self.assertIs(owner['active_support'], active_support)


class SuccessTests(unittest.TestCase):
    def evidence(self, **updates):
        values = dict(all_bottom_corners_clear=True, independent_view_confirms=True,
                      visible_support_gap=True, slipping=False, hold_duration=5.,
                      required_duration=4., verified_reference=True, lower_bound=.8,
                      required_clearance=.7)
        values.update(updates)
        return values

    def test_complete_evidence_passes(self):
        require_verified_lift(**self.evidence())

    def test_stable_suspension_alone_is_not_metric_success(self):
        values = self.evidence(verified_reference=False)
        require_lift_evidence(**{k: v for k, v in values.items()
                              if k not in ('verified_reference', 'lower_bound', 'required_clearance')})
        with self.assertRaises(RuntimeError):
            require_verified_lift(**values)

    def test_each_missing_condition_blocks_full_claim(self):
        for updates in (dict(all_bottom_corners_clear=False), dict(independent_view_confirms=False),
                        dict(visible_support_gap=False), dict(slipping=True),
                        dict(hold_duration=3.), dict(lower_bound=.6)):
            with self.subTest(updates=updates), self.assertRaises(RuntimeError):
                require_verified_lift(**self.evidence(**updates))

    def test_invalid_durations_cannot_bypass_gate(self):
        for key in ('hold_duration', 'required_duration'):
            for value in (-1., math.nan, math.inf):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    require_verified_lift(**self.evidence(**{key: value}))
        with self.assertRaises(ValueError):
            require_verified_lift(**self.evidence(required_duration=0.))


if __name__ == '__main__':
    unittest.main(verbosity=2)
