---
name: fresh-robot-grasp
description: Fresh-observation procedures and generic low-level sensor and safety helpers for an XLeRobot grasp session.
---

# Fresh robot grasp procedure

## Transfer boundary

This directory contains general procedures and generic code only. It contains no
observations, calibration, scene geometry, motor targets, movement directions,
recorded joint values, trajectories, images, or replay data. Transfer only this
cleaned directory. Derive every movement target and device role anew.

Keep logs, screenshots, measurements, task scripts, reports, and audits outside
this directory. Do not open previous conversations, memories, task workspaces,
run evidence, task calibration files, or Git history. Stop safely and report
contamination if prohibited historical information is encountered.

Use only low-level motor and camera modules from the permitted XLeRobot/LeRobot
projects. Existing environments and generic drivers are startup infrastructure.
Do not load robot model files, existing kinematics or grasp implementations,
simulations, demonstrations, datasets, policies, or external reference material.

## Discovery and startup

- Inspect the current workspace and copied skill before acting. Initialize Git
  at the workspace root without inspecting history.
- Check current device nodes and live sysfs metadata. Missing sandbox device
  nodes do not establish that host hardware is absent. Request approved
  sandbox-escalated, read-only host device enumeration when necessary.
- Read only the required low-level driver sources. Establish device roles from
  fresh hardware responses, current views, and generic wiring declarations.
  Do not import a complete robot controller that can load saved calibration.
- Keep discovery separate from assigned motor access. Some drivers cache ID and
  model lookups at construction. After a discovery scan, close that connection
  and construct a new bus with the freshly verified assignments instead of
  replacing its motor dictionary in place.
- Capture fresh wrist and overview views. Read current mode, model, position,
  load, temperature, status, torque state, and configured hardware limits.
- When a motor is disabled, load its freshly read position before enabling it.
  When it is already enabled, preserve its current goal unless an intentional
  change has been justified. Restarting a monitor must not release a grasp.
- Freeze the observation arm's goal and monitor its drift. Avoid writes to the
  base, head, or other unrelated actuators.
- Before motion, check that the actual command owner invokes the required
  health, drift, goal-continuity, and retention gates. A helper's presence in this
  directory does not establish runtime enforcement. Exercise missing feedback,
  stale evidence, and preload-loss handling offline with synthetic inputs.

## Execution

- Use a local process to own the serial buses and monitor health between online
  decisions. Do not let independent processes write to the same motor bus.
- Confirm that the command channel remains open and that the monitor is alive
  before the first motion. End-of-input can terminate a controller while servo
  torque remains enabled. A lost tool session handle does not establish process
  exit; inspect only the current session's matching process before taking over.
  Track monitoring gaps separately from actuator motion. After a confirmed
  process exit, reconcile pending commands before resuming: a queued shutdown
  intended for the old owner can otherwise immediately stop the replacement.
  Use an advisory ownership lock for cooperating utilities and preserve the
  live goals across handover. The lock cannot exclude unrelated controllers.
- Start with small, visible probes. Identify direction and effect from fresh
  images and feedback. Use conservative velocity, acceleration, travel, and
  effort bounds; never overwrite protective limits to make a move succeed.
- Capture images after meaningful segments. Batch only operations whose safety
  follows from the same observations. Stop when clearance or feedback is unclear.
  Closure, the first test lift, and further lift extension are separate decisions:
  each needs evidence of the preceding result before it can be authorized.
- Treat command labels as intentions, never as evidence of motion or success.
  Check the resulting geometry before proceeding. If the object follows an arm
  alignment move, contact remains; do not treat that move as free-space alignment.
- Establish a visible gap before moving laterally around an object. Open enough
  that the complete swept finger shape clears the object, including the moving
  finger's changing reach. Opening alone can move an object that remains hooked.
- A proportional servo can settle short of a goal. Distinguish settling from
  reaching the requested target, use the actual measured pose for the next
  decision, and do not drive harder merely to satisfy an arbitrary tolerance.
- Preserve the active position goals when starting a loaded motion segment.
  A measured position can differ from the goal because it is supporting a load.
  Replacing that goal with the measurement can relax support before the next
  segment begins. Derive the destination from fresh observations, but interpolate
  from the active command and monitor the actual response independently.
- Paired joint changes do not guarantee constant height, direction, or wrist
  inclination. Their effects vary with configuration and tracking error. Use
  independent fresh views to check actual motion; avoid long chains of assumed
  compensations and increasingly ambiguous corrective moves.
- If repeated corrections still fail to establish clear enclosure, withdraw to
  visible free space and reassess or end safely. Do not continue contact-based
  alignment merely because motor health readings remain acceptable.
  State what new observation justifies each correction. If the grasp is uncertain,
  preserve support while assessing a safe return to the surface; confirm support
  before releasing or withdrawing. Do not invent an automatic recovery movement.
- Treat a temperature anomaly as a reason to pause and investigate. A sudden
  transient may indicate a sensor or communication problem, but does not justify
  ignoring subsequent alarms or disabling thermal protection.
  Record the anomalous reading outside this directory and corroborate it with
  repeated individual register reads while motion is paused. An operator's
  explanation can inform the diagnosis; preserve existing protection registers
  and continue checking subsequent readings rather than suppressing the sensor.

## Grasp and lift verification

- Wrist-image overlap alone does not establish insertion depth. Confirm from an
  independent view that both fingers extend alongside the object before closure.
- Confirm that both inner faces overlap opposing side walls below the upper
  edges. Finger tips projected onto a top face are not side enclosure. Inspect
  the whole near and far edges, not just an apex or a partially occluded outline.
- Check insertion along the finger length separately from contact height. A
  finger projected across the lower body can still touch only an end corner.
  Require visible overlap along both inner faces through the closing arc;
  tip contact and small object displacement do not establish that overlap.
- Account for a moving finger's arc: its open tip can extend farther forward than
  its closing tip. Shallow contact can rotate or push the object without grasping.
- Reobserve after any object displacement. Preserve desk clearance while
  correcting insertion depth and alignment.
- Rolling or tipping under light closure often indicates misplaced contact.
  Re-establish clear space and side-wall engagement rather than repeatedly
  closing, changing yaw, or descending while a finger catches an upper edge.
- Close slowly with limited effort and bounded travel. Require sustained contact
  evidence away from the freshly observed closed limit, plus visible enclosure.
  Contact with a finger stop is not a grasp. Do not automatically lift on load alone.
- Stable nonzero effort and a small tracking shortfall can occur during edge
  contact or object rotation. They are supporting signals, not proof of a secure
  grasp. Require enclosure first, then check that preload and object position
  persist through a small lift before extending the lift.
- Preserve gripper preload during arm stops and controller restarts. Holding an
  encoder position after reducing preload can leave an object partly supported
  by the table despite apparently stable feedback.
- Recheck object position relative to the fingers and sustained preload after
  the first small lift, before extending it. Rotation or settling within the
  fingers invalidates the earlier contact assessment even if the object appears
  upright afterward. Stop further lifting on loss of preload or enclosure;
  use short segments and timely visual observations to limit an undetected slip.
  Monitor preload loss during the segment as an early warning, without
  automatically tightening the fingers to compensate for an uncertain grasp.
  Check every acquired effort sample, including intermediate drops followed by
  recovery, against both fresh absolute and relative retention bounds. Verify
  the closing-effort direction; raw effort is not a calibrated force. Missing,
  delayed, or nonfinite feedback cannot authorize more travel. Latch a failed
  check locally, inhibit further progression, and preserve the active support
  goals while reassessing; do not automatically open or remove torque. A later
  good sample must not clear the latch. Other hardware faults may require a
  different stop response; a preload gate is not a complete safety controller.
  A carton may slowly rotate or settle while both encoder position and effort
  remain steady. Compare fresh images after a stationary dwell before extending
  a test lift. If an adjustment is warranted, first establish surface support,
  then use bounded effort and travel, and rebuild the complete grasp assessment.
- Account for actual direction changes and tracking shortfall independently at
  each joint. A paired command can rotate the wrist before the lifting joint
  moves enough, pressing or tilting an object that still touches the desk.
- Lift enough to establish an unambiguous gap under the entire base, including
  the farthest corner. Check independent views, the bottom silhouette, and the
  separation from the support surface. A shadow or one raised corner is not
  sufficient evidence that the object is fully suspended.
- Verify sustained clearance, no slipping, and stable arm feedback over a timed
  hold. Encoders alone cannot establish object stability or full clearance.
  Save independent views at both ends of the reported interval, and summarize
  the intervening telemetry. State that visual sampling and continuous feedback
  are different forms of evidence; do not imply continuous visual verification
  when only endpoint images were inspected.
  Establish the observation arm's reference from its current feedback, retain
  every monitored joint in each sample, and reject missing or nonfinite values.
- Establish an allowed metric reference from fresh observations before claiming
  a metric clearance. Pixel gaps and uncalibrated joint displacements alone do
  not prove an absolute distance. Keep measurements and reference evidence out
  of the transfer directory.
  Check that such a reference is available during startup when the task has a
  metric success threshold. Report stable suspension and metric verification
  separately if the allowed observations cannot establish an absolute scale.
- Report uncertainty honestly. Correct a mistaken outcome claim explicitly and
  continue the same attempt when a safe correction remains possible.

## Evidence validity and decision cost

Treat every enclosure or retention assessment as evidence for a particular
observed state. Object motion within the fingers, slip, opening or regripping,
preload adjustment, uncertain contact, or lost camera coverage invalidates it.
Acquire new independent views after the invalidating event, rebuild the preload
window, and reassess before extending the lift. Do not carry an old "secure"
assessment forward or relabel a cached image as fresh. Use acquisition timestamps
from a consistent monotonic clock and runtime age bounds for control decisions.

Restart the reported stability interval after any settling, grip adjustment, or
loss of evidence. Full task success requires all requested conditions together:
whole-base clearance, retained enclosure, no observed slip, a qualifying hold,
acceptable feedback and observation-arm drift, and a verified lower clearance
bound when a metric threshold is requested. Motor health, joint immobility, or
a larger commanded lift cannot substitute for missing geometric evidence or scale.

Reduce online overhead by returning current telemetry, independent fresh views,
and segment completion status together. Batch free-space segments only when
current evidence covers their entire swept motion. Keep local health and
retention monitoring active between decisions. Avoid redundant stationary tool
polls; do not remove contact-transition checks or raise speed to save decisions.

## Closeout

Keep the requested final hold only with the necessary motor goals and protections
preserved. Closing a serial connection must not inadvertently disable torque or
open a loaded gripper. Do not assume that removing torque is always a safe stop.
Explicitly distinguish ending software monitoring from removing motor torque.
Report whether a loaded hold remains active at closeout. Read protection registers
again after execution and compare them with the fresh startup snapshot.

Treat the entire session as one attempt. After success or final safe termination,
update this skill and reusable code, manually review every transfer file, run an
audit for prohibited data, and commit all current-workspace changes once. Do not
rewrite history. Report outcome, actual verification interval, elapsed time, and
clearly defined online decision counts, including corrections and diagnostic pauses.
Record the first commanded motion and first observed motion separately, then
identify the final qualifying verification evidence. Keep diagnostic, recovery,
and observation delays in elapsed wall time; distinguish this from commanded
motion duration. A withdrawn success claim cannot be the completion endpoint.
If only an observation request is timestamped, label it as a timing proxy, not
the exact confirmation time. Count submitted and completed movement commands,
online batches, recovery commands, supervisory decisions, and human interventions
separately. Failure has no successful completion time. Do not compare unlike
decision-count definitions or infer improvement from elapsed time alone.

An operator's stop ends grasp recovery. Stop the motion owner before transferring
serial ownership to a release utility. When the operator requests torque removal,
disable the requested motors and read back their torque state; do not infer
release from process exit. Preserve temperature protection settings rather than
changing them on the basis of an unverified material claim.

## Reusable helpers

`hardware.py` provides read-only discovery, telemetry, fresh camera capture, and
an explicit torque-release helper for operator-directed shutdown.
`safety.py` provides parameterized checks; it contains no movement targets or
scene-specific thresholds. Neither helper is an autonomous grasp controller.
Supply all runtime device assignments, thresholds, and evidence from the current
session. Save output outside this directory.

The retention check requires fresh independent visual confirmation as well as
preload persistence. Its numeric inputs are runtime evidence and bounds, not
transferable grasp settings. Test these gates with synthetic values only, and
keep test outputs outside this directory.
`require_fresh_evidence` rejects stale or invalidated observations.
`require_preload_window` checks continuity and every sampled effort, including
losses hidden by recovered endpoints. Invoke it in the local monitoring loop;
catching and ignoring its exception defeats the gate. It retains no fault state:
the command owner must latch failure until deliberate reassessment establishes
new evidence. `require_verified_lift` combines visual hold and metric clearance
checks; it must receive evidence for the same current hold. None of these helpers
infers geometry, chooses movement targets, or proves safety between samples.

The active-goal reader and continuity check support loaded segment transitions.
The temperature confirmation helper reads individual registers without changing
protection settings. Neither helper decides that a contact is a secure grasp or
that a sensor anomaly is harmless. All conclusions require current evidence.
The fixed-joint hold check verifies complete finite feedback against a fresh
runtime reference. The protection comparison detects changes between fresh
register snapshots. Neither check establishes object clearance or safe indefinite
holding, and neither writes motor registers.
The motor-health gate rejects missing and nonfinite feedback and invalid bounds;
ordinary numeric comparisons alone can silently accept a nonfinite sensor value.
The advisory command-owner helper acquires a runtime lock outside the transfer
directory. It is a coordination primitive, not a proof of exclusive hardware
ownership or a replacement for checking the previous process's status.

Before transfer, remove bytecode caches and other generated files from this
directory. Review every source file and reject unreviewed binaries, symlinks,
runtime assignments, identifiers, targets, or observation data. An automated
scan supplements manual review; it does not prove that encoded data is absent.
