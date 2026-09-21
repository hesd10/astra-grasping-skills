"""Generic parameterized checks. No recorded state, targets, or trajectories."""
import math


def require_healthy(sample, temperature_limit, temperature_margin, load_limit):
    if sample['Status']:
        raise RuntimeError('Motor reports a status fault')
    if sample['Present_Temperature'] >= temperature_limit - temperature_margin:
        raise RuntimeError('Temperature is too close to the configured limit')
    if abs(sample['Present_Load']) > load_limit:
        raise RuntimeError('Motor effort exceeds the current safety bound')


def require_contact_evidence(*, sustained_load, tracking_shortfall,
                             distance_from_closed_limit, minimum_load,
                             minimum_shortfall, closed_limit_margin,
                             visible_enclosure):
    if not visible_enclosure:
        raise RuntimeError('Object enclosure has not been established')
    if distance_from_closed_limit <= closed_limit_margin:
        raise RuntimeError('Contact near the closed stop cannot establish a grasp')
    if sustained_load < minimum_load or tracking_shortfall < minimum_shortfall:
        raise RuntimeError('Insufficient sustained contact evidence')


def require_side_enclosure(*, opposing_side_walls_engaged,
                           upper_edges_clear, sufficient_insertion,
                           independent_view_confirms, object_moved):
    """Supply conclusions from fresh views; this does not infer geometry."""
    if object_moved:
        raise RuntimeError('Reobserve the displaced object before relying on enclosure')
    if not independent_view_confirms:
        raise RuntimeError('An independent view has not confirmed side enclosure')
    if not (opposing_side_walls_engaged and upper_edges_clear and sufficient_insertion):
        raise RuntimeError('Edge contact or shallow overlap is not secure side enclosure')


def require_lift_evidence(*, all_bottom_corners_clear, independent_view_confirms,
                          visible_support_gap, slipping, hold_duration,
                          required_duration):
    if not all(math.isfinite(value) for value in (hold_duration, required_duration)):
        raise ValueError('Hold durations must be finite')
    if hold_duration < 0 or required_duration <= 0:
        raise ValueError('Observed duration must be nonnegative and required duration positive')
    if not (all_bottom_corners_clear and independent_view_confirms and visible_support_gap):
        raise RuntimeError('Full support-surface clearance has not been established')
    if slipping:
        raise RuntimeError('Object is slipping')
    if hold_duration < required_duration:
        raise RuntimeError('Verified hold interval is too short')


def require_fresh_evidence(*, observed_at, now, maximum_age, invalidated_at=None):
    """Use actual acquisition times from one current-session monotonic clock.

    Re-reading cached evidence must not advance its acquisition time. A pass
    establishes recency only; the caller still has to evaluate the evidence.
    """
    if not all(math.isfinite(value) for value in (observed_at, now, maximum_age)):
        raise ValueError('Evidence timing must be finite')
    if observed_at < 0 or now < observed_at or maximum_age <= 0:
        raise ValueError('Evidence timing or age bound is invalid')
    if invalidated_at is not None:
        if not math.isfinite(invalidated_at) or not 0 <= invalidated_at <= now:
            raise ValueError('Invalidation must use the same current clock')
        if observed_at <= invalidated_at:
            raise RuntimeError('Evidence predates the latest invalidating event')
    if now - observed_at > maximum_age:
        raise RuntimeError('Evidence is too old to authorize progression')


def require_preload_window(samples, *, now, maximum_age, minimum_duration,
                           maximum_gap, baseline_preload, minimum_preload,
                           maximum_fractional_loss, invalidated_at=None):
    """Check timestamp/closing-effort pairs, including intermediate losses.

    Supply a freshly measured, visually supported baseline and freshly verified
    effort direction. Effort units are not calibrated force. Check before and
    during motion with bounds established for this session. The caller must
    latch a failure and inhibit progression; a later passing window must not
    clear it automatically. This function neither writes motors nor verifies
    geometry and is not a complete slip-prevention controller.
    """
    if len(samples) < 2:
        raise ValueError('Repeated preload samples are required')
    bounds = (minimum_duration, maximum_gap, baseline_preload,
              minimum_preload, maximum_fractional_loss)
    if not all(math.isfinite(value) for value in bounds):
        raise ValueError('Preload bounds must be finite')
    if min(minimum_duration, maximum_gap, baseline_preload, minimum_preload) <= 0:
        raise ValueError('Positive duration, gap, preload, and minimum bounds are required')
    if not 0 <= maximum_fractional_loss < 1:
        raise ValueError('Fractional loss bound must lie in the unit interval')
    first_time = None
    previous_time = None
    for observed_at, effort in samples:
        if not all(math.isfinite(value) for value in (observed_at, effort)):
            raise ValueError('Preload samples must be finite')
        if observed_at < 0:
            raise ValueError('Sample times must be nonnegative')
        if previous_time is not None:
            if observed_at <= previous_time:
                raise ValueError('Samples must have strictly increasing acquisition times')
            if observed_at - previous_time > maximum_gap:
                raise RuntimeError('Missing preload observations prevent progression')
        else:
            first_time = observed_at
        if effort < minimum_preload:
            raise RuntimeError('Preload fell below the current minimum')
        if effort < baseline_preload * (1 - maximum_fractional_loss):
            raise RuntimeError('Preload loss requires stopping and reobserving')
        previous_time = observed_at
    require_fresh_evidence(observed_at=previous_time, now=now,
                           maximum_age=maximum_age, invalidated_at=invalidated_at)
    if invalidated_at is not None and first_time <= invalidated_at:
        raise RuntimeError('Rebuild the preload window after invalidation')
    if now - previous_time > maximum_gap:
        raise RuntimeError('The preload sampling stream has stopped')
    if previous_time - first_time < minimum_duration:
        raise RuntimeError('Preload observation interval is too short')


def require_grasp_retention(*, opposing_walls_still_engaged,
                            independent_view_confirms, object_moved_in_gripper,
                            preload_before, preload_now, minimum_preload,
                            maximum_fractional_loss):
    """Gate further lifting from fresh evidence; never supply stored observations.

    Effort is only a supporting signal. A pass is not a force measurement or
    geometric proof, and the caller must establish its bounds for the session.
    """
    if not independent_view_confirms or not opposing_walls_still_engaged:
        raise RuntimeError('Grasp enclosure has not persisted through the lift')
    if object_moved_in_gripper:
        raise RuntimeError('Object movement within the fingers requires a stop')
    if not all(math.isfinite(value) for value in
               (preload_before, preload_now, minimum_preload, maximum_fractional_loss)):
        raise ValueError('Retention inputs must be finite')
    if not (preload_before > 0 and minimum_preload > 0):
        raise ValueError('Positive observed preload and required bound are necessary')
    if not 0 <= maximum_fractional_loss < 1:
        raise ValueError('Fractional loss bound must lie in the unit interval')
    if preload_now < minimum_preload:
        raise RuntimeError('Preload is insufficient to extend the lift')
    if preload_now < preload_before * (1 - maximum_fractional_loss):
        raise RuntimeError('Preload loss requires stopping and reobserving')


def require_goal_continuity(active_goals, segment_start_goals):
    """Prevent an unnoticed command change at a loaded segment boundary."""
    if set(active_goals) != set(segment_start_goals):
        raise ValueError('The active and segment motor sets must match')
    if not all(math.isfinite(value) for value in
               list(active_goals.values()) + list(segment_start_goals.values())):
        raise ValueError('Goal values must be finite')
    if active_goals != segment_start_goals:
        raise RuntimeError('A loaded segment must start from its active goals')


def require_metric_clearance(*, verified_reference, lower_bound,
                             required_clearance):
    """Gate a metric claim; image visibility and grasp stability are separate."""
    if not verified_reference:
        raise RuntimeError('No verified current metric reference is available')
    if not all(math.isfinite(value) for value in (lower_bound, required_clearance)):
        raise ValueError('Clearance bounds must be finite')
    if required_clearance <= 0 or lower_bound < required_clearance:
        raise RuntimeError('The measured lower bound does not establish clearance')


def require_verified_lift(*, all_bottom_corners_clear, independent_view_confirms,
                          visible_support_gap, slipping, hold_duration,
                          required_duration, verified_reference, lower_bound,
                          required_clearance):
    """Require both stable visual suspension and a measured clearance bound.

    Inputs must describe the same fresh hold interval. Health, grasp retention,
    evidence freshness, and observation-arm drift remain separate checks.
    """
    require_lift_evidence(all_bottom_corners_clear=all_bottom_corners_clear,
                          independent_view_confirms=independent_view_confirms,
                          visible_support_gap=visible_support_gap, slipping=slipping,
                          hold_duration=hold_duration, required_duration=required_duration)
    require_metric_clearance(verified_reference=verified_reference,
                             lower_bound=lower_bound, required_clearance=required_clearance)


def require_fixed_joint_hold(position_samples, reference_positions, maximum_drift):
    """Check current-session feedback; this does not verify object stability."""
    if not position_samples or not reference_positions:
        raise ValueError('A reference and observed samples are required')
    if not math.isfinite(maximum_drift) or maximum_drift < 0:
        raise ValueError('The drift bound must be finite and nonnegative')
    if not all(math.isfinite(value) for value in reference_positions.values()):
        raise ValueError('Reference positions must be finite')
    for sample in position_samples:
        if set(sample) != set(reference_positions):
            raise ValueError('Every sample must contain all monitored joints')
        for joint, value in sample.items():
            if not math.isfinite(value):
                raise ValueError('Observed positions must be finite')
            if abs(value - reference_positions[joint]) > maximum_drift:
                raise RuntimeError('Observed joint drift exceeds the runtime bound')


def require_protection_unchanged(before, after):
    """Compare freshly read protection settings without writing registers."""
    if not before or not after:
        raise ValueError('Both protection snapshots are required')
    if before != after:
        raise RuntimeError('Hardware protection settings changed during the session')
