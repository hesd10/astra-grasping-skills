"""Generic parameterized checks. No recorded state, targets, or trajectories."""


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


def require_lift_evidence(*, all_bottom_corners_clear, independent_view_confirms,
                          visible_support_gap, slipping, hold_duration,
                          required_duration):
    if not (all_bottom_corners_clear and independent_view_confirms and visible_support_gap):
        raise RuntimeError('Full support-surface clearance has not been established')
    if slipping:
        raise RuntimeError('Object is slipping')
    if hold_duration < required_duration:
        raise RuntimeError('Verified hold interval is too short')
