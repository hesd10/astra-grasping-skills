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
- Capture fresh wrist and overview views. Read current mode, model, position,
  load, temperature, status, torque state, and configured hardware limits.
- When a motor is disabled, load its freshly read position before enabling it.
  When it is already enabled, preserve its current goal unless an intentional
  change has been justified. Restarting a monitor must not release a grasp.
- Freeze the observation arm's goal and monitor its drift. Avoid writes to the
  base, head, or other unrelated actuators.

## Execution

- Use a local process to own the serial buses and monitor health between online
  decisions. Do not let independent processes write to the same motor bus.
- Start with small, visible probes. Identify direction and effect from fresh
  images and feedback. Use conservative velocity, acceleration, travel, and
  effort bounds; never overwrite protective limits to make a move succeed.
- Capture images after meaningful segments. Batch only operations whose safety
  follows from the same observations. Stop when clearance or feedback is unclear.
- Treat command labels as intentions, never as evidence of motion or success.
  Check the resulting geometry before proceeding. If the object follows an arm
  alignment move, contact remains; do not treat that move as free-space alignment.
- Establish a visible gap before moving laterally around an object. Open enough
  that the complete swept finger shape clears the object, including the moving
  finger's changing reach. Opening alone can move an object that remains hooked.
- A proportional servo can settle short of a goal. Distinguish settling from
  reaching the requested target, use the actual measured pose for the next
  decision, and do not drive harder merely to satisfy an arbitrary tolerance.
- Paired joint changes do not guarantee constant height, direction, or wrist
  inclination. Their effects vary with configuration and tracking error. Use
  independent fresh views to check actual motion; avoid long chains of assumed
  compensations and increasingly ambiguous corrective moves.
- If repeated corrections still fail to establish clear enclosure, withdraw to
  visible free space and reassess or end safely. Do not continue contact-based
  alignment merely because motor health readings remain acceptable.
- Treat a temperature anomaly as a reason to pause and investigate. A sudden
  transient may indicate a sensor or communication problem, but does not justify
  ignoring subsequent alarms or disabling thermal protection.

## Grasp and lift verification

- Wrist-image overlap alone does not establish insertion depth. Confirm from an
  independent view that both fingers extend alongside the object before closure.
- Confirm that both inner faces overlap opposing side walls below the upper
  edges. Finger tips projected onto a top face are not side enclosure. Inspect
  the whole near and far edges, not just an apex or a partially occluded outline.
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
- Lift enough to establish an unambiguous gap under the entire base, including
  the farthest corner. Check independent views, the bottom silhouette, and the
  separation from the support surface. A shadow or one raised corner is not
  sufficient evidence that the object is fully suspended.
- Verify sustained clearance, no slipping, and stable arm feedback over a timed
  hold. Encoders alone cannot establish object stability or full clearance.
- Establish an allowed metric reference from fresh observations before claiming
  a metric clearance. Pixel gaps and uncalibrated joint displacements alone do
  not prove an absolute distance. Keep measurements and reference evidence out
  of the transfer directory.
- Report uncertainty honestly. Correct a mistaken outcome claim explicitly and
  continue the same attempt when a safe correction remains possible.

## Closeout

Keep the requested final hold only with the necessary motor goals and protections
preserved. Closing a serial connection must not inadvertently disable torque or
open a loaded gripper. Do not assume that removing torque is always a safe stop.

Treat the entire session as one attempt. After success or final safe termination,
update this skill and reusable code, manually review every transfer file, run an
audit for prohibited data, and commit all current-workspace changes once. Do not
rewrite history. Report outcome, actual verification interval, elapsed time, and
clearly defined online decision counts, including corrections and diagnostic pauses.

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

Before transfer, remove bytecode caches and other generated files from this
directory. Review every source file and reject unreviewed binaries, symlinks,
runtime assignments, identifiers, targets, or observation data. An automated
scan supplements manual review; it does not prove that encoded data is absent.
