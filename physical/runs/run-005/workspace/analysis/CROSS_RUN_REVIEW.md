# Retrospective comparison of Runs 001–005

The series produced three visually stable suspensions and two failed grasps.
**None of the five runs verified the original absolute clearance requirement of
at least 3 cm.** Stable suspension is therefore a partial result, not full metric
success. The first project's current name is `Run 001`; its report and logs still
contain some paths with its former name, `Run 001 6`. Those historical records
have not been rewritten.

This review uses the user's explicit authorization to compare prior skill files,
reports, and execution evidence. No robot operations, previous conversations,
external references, or new physical experiments were used. All comparative
measurements and source links stay here, outside the transferable `skill/`.

## Results and comparable timing

| Run | Process and result | Observed final stable hold | First logged movement → final hold evidence | Submitted movement commands |
| --- | --- | ---: | ---: | ---: |
| 001 | Shallow alignment and closure needed correction. An initial success claim was withdrawn after the user identified a bottom corner still touching the desk. Preserved preload and a further lift produced full visible suspension. | 36.81 s | 25 min 18 s | 31 in 29 actuation batches |
| 002 | Initial lift moved the carton; the next lift slipped. Seventeen subsequent recovery commands produced edge contact, rotation, and rolling without a stable grasp. Operator ended recovery. | 0 s | No successful completion | 35 |
| 003 | Small lift looked tentatively plausible; extension lost the grasp. Effort fell during that segment, and segment-end images established the failure. Operator then requested release. | 0 s | No successful completion | 25, plus one diagnostic hold |
| 004 | First closure tilted the carton. A later light grasp settled; the carton was returned to support before preload adjustment, a revised test lift, and extension. Final suspension was stable. | 65.80 s | About 21 min 30 s, observation-request proxy | 31 submitted; 30 completed and one blocked |
| 005 | Probes and approach led to closure and a sequence of short lifts. Early lift commands produced little actual lifting-joint travel. Final suspension was stable, with no fault-recovery commands. | 53.61 s | 13 min 44 s | 25 |

“First logged movement” is the first left-arm position sample that changes after
the first movement command, compared with the latest preceding sample. This is
a reproducible telemetry marker, not an exact physical motion-onset measurement.
The endpoint is the final qualifying hold evidence, after any corrections. It is
not the timestamp of a subsequent assistant message declaring success, which is
not established by these files. All pauses, observation delays, recovery, and
interventions between the markers remain in the elapsed time. Setup, later
closeout, documentation, and commits are excluded.

| Run | First changed sample, UTC | Final evidence marker, UTC | Exact derived interval |
| --- | --- | --- | ---: |
| 001 | 2026-09-15 16:23:22.710852 | 2026-09-15 16:48:40.546650, final corrected snapshot | 1517.835798 s |
| 004 | 2026-09-16 01:38:22.609082 | 2026-09-16 01:59:52.873329, hold-end observation request | 1290.264247 s |
| 005 | 2026-09-16 02:22:40.181675 | 2026-09-16 02:36:24.224400, hold-end image event | 824.042726 s |

Run 004 does not log the image-completion time at that endpoint, so its marker
slightly precedes completion of the observation. Its reported hold interval also
uses that request marker. Exact assistant-confirmation times are unavailable for
all three, and **time to full metric success is unavailable for every run**.
Hold durations describe endpoint visual observations supported by intervening
telemetry, not continuous visual proof. Failure runs are not assigned a short
“success time.”

The right arm remained at its observation reference within the reported feedback:
maximum drift was one raw count in Run 001 and zero in Runs 002–005. Reports found
no obvious robot or environmental damage in the inspected views; this is not a
physical inspection. Post-attempt torque release is separate from grasp outcome.
Run 005 already records all twelve arm/gripper motors released at the user's
request; this retrospective neither rechecks nor changes hardware state.

## Process differences and what the existing iterations added

| Run | Material process observations | Skill contribution at that run's closeout |
| --- | --- | --- |
| 001 | Fresh start; sandbox device visibility differed from host availability. Tracking pauses, an anomalous temperature sample, and user correction complicated execution. A stationary arm did not prove full clearance. | Established the clean transfer boundary, live device discovery, exclusive low-level ownership, bounded probes, preload preservation, independent views, whole-base clearance, timed verification, and safe closeout. |
| 002 | Projected overlap, effort, and tracking shortfall were overtrusted. Recovery continued while the fingers remained in contact and moved the carton. | Added opposing side-wall enclosure, complete finger sweep clearance, reobservation after displacement, limits on ambiguous contact corrections, metric-reference cautions, and explicit torque-off readback. |
| 003 | Driver lookup caching and closed command input required startup corrections. A plausible small lift did not retain the grasp during extension. | Added fresh bus reconstruction, command-channel liveness, insertion-depth checks, retention after a test lift, relative preload loss, and separate checks of actual joint response. |
| 004 | A temperature anomaly caused a pause and blocked command; continuation followed individual reads and user input. Loaded goal continuity and returning a settling grasp to support mattered. | Added preservation of active goals across loaded transitions, individual-read temperature corroboration, goal continuity and metric-clearance gates, and checking metric observability at startup. |
| 005 | A shorter sequence reached stable suspension without recovery; tracking shortfall still affected initial lift commands. Verification used endpoint views and 255 telemetry samples. | Added complete finite fixed-joint hold checks, unchanged-protection comparison, clearer endpoint-versus-continuous visual evidence, and explicit monitoring/torque closeout distinctions. |

These entries describe additions observed in successive skill files and reports;
they do not prove that every procedure was enforced in each live controller.
The present retrospective update is separate from the original Run 005 closeout.

Decision counts need consistent definitions. Run 001 reported 29 actuation
batches containing 31 commands, plus five starts/resumes, three sensor passes,
one verification snapshot, and two closes. Run 003 reported 24 online batches
containing 25 movements and one stationary hold, with two startup corrections
separate. Run 004 reported 31 movement submissions plus five supervisory groups.
Run 005 reported 25 movements plus three startup groups, verification, and
closeout, totaling 30 operational groups. These totals should not be ranked as
if they measured identical interventions. Run 001 included a human clearance
correction; Run 004 included a human continuation instruction. Operator-directed
termination and later torque release are separate interventions.

## Lessons supported by comparison

### Make contact-to-lift transitions explicit decision boundaries

Runs 002 and 003 both lost the object when extending an initially plausible lift.
Run 002's gripper feedback decreased from 64 at `secure_contact` to 56 at
`initial_lift` and 32 at `clearance_lift`. In Run 003, step 26 began at 76, reached
a minimum of 31, and ended at 36; preceding small-lift segments retained 76.
These are uncalibrated raw effort observations, not force measurements or future
grip settings. Together with the documented slips, they motivate monitoring
retention during movement rather than accepting only endpoint effort or the
original closure assessment.

The new procedure requires separate evidence after closure, after the small test
lift, and before extension. A continuous sampling window must reject inadequate
effort, excessive relative loss, stale samples, and gaps. A recovered endpoint
must not erase an earlier loss. No historical thresholds, directions, or targets
are transferred.

### Invalidate assessments after object motion or grip changes

Run 002's contact corrections repeatedly changed the object state. Run 003's
tentative small lift did not justify extension once retention was uncertain.
Run 004 established a new support/grip state before its successful final lift.
The transferable rule is to discard stale enclosure and retention assessments
after displacement, settling, opening, regripping, preload adjustment, or lost
coverage. Acquire fresh independent evidence, rebuild the preload window, and
restart the verified hold interval. A correction should be justified by new
evidence, not by a favorable command label.

### Check enforcement in the actual command owner

Run 003's report explicitly records that its monitor did not halt on relative
preload loss during a segment. Run 004's retained controller includes an optional
`minimum_preload` check within its movement loop. Run 005's retained controller
does not include a corresponding lower-preload or fractional-loss gate, although
the skill already contained a retention helper. Its saved `check` function covers
status, maximum effort, torque state, and observation-arm drift; temperatures
are logged, but that function has no supervisory temperature comparison.
The reports record unchanged hardware temperature protection.

Saved source is evidence of the retained implementation, not a complete versioned
trace proving every instruction executed during every phase. The broader finding
is nevertheless concrete: helper availability and successful suspension do not
demonstrate runtime coverage. The updated skill requires a preflight check of
the actual command owner and synthetic fault injection. A preload failure must
latch and inhibit progression; it must not automatically tighten, open the
gripper, remove torque, or clear itself after a good sample. The new helper
provides the check; a future controller must integrate the latch and stop response.

### Treat recoveries and incomplete progress as new evidence problems

Run 002 spent 17 additional commands on recovery without a verified grasp.
Run 004 returned a settling grasp to support before changing preload. Run 005's
first lift commands illustrate that requested joint travel and actual object
movement can differ substantially. These comparisons support confirming support
before release, establishing visible free space before alignment, preserving
active support goals, and checking actual joint and object response separately.
They do not establish a universal recovery trajectory or a safe fixed retry count.

### Compose the complete success criterion

Run 001's first claim failed even visual whole-base clearance; its later corrected
hold is the appropriate endpoint. Every run lacked metric certification. Repeated
success at suspension cannot solve an unmeasured scale requirement. The new
composite gate requires both visual hold evidence and an adequate measured lower
clearance bound. Freshness, retention, hardware health, and observation-arm checks
remain additional requirements. If a permitted metric reference is unavailable,
report that limitation and the partial result without calling the full task done.

### Reduce observation and dispatch overhead before changing motor speed

Run 005 was the shortest of the three runs that achieved stable suspension.
Its 25 declared movement segments total 83 seconds; the sum of each command's
timestamp to its matching image-result event is 97.30 seconds, compared with
824.04 seconds from first observed movement to hold-end evidence. The remaining
interval includes observation, model/tool delays, the verification hold, and
other unpartitioned time. It is not all reasoning time or avoidable overhead.

This suggests returning telemetry, fresh independent images, and completion
status together, and avoiding redundant stationary polling. Batching remains
appropriate only where existing evidence covers the full motion. Closure, test
lift, and extension must retain their intervening observation gates. No faster
motor settings can be justified from this comparison.

These five experiments had different initial conditions, runtime revisions,
pauses, and human involvement. The outcomes are not monotonic, and the comparison
does not demonstrate a causal learning curve or estimate a reliable success rate.
The new procedures and code have offline validation only; no sixth physical
attempt was conducted.

## Changes and verification in this retrospective

- `skill/SKILL.md`: added runtime enforcement checks, transition boundaries,
  evidence invalidation, local failure latching, support-aware recovery rules,
  observation/dispatch efficiency, and comparable outcome/timing accounting.
- `skill/safety.py`: added `require_fresh_evidence`, `require_preload_window`, and
  `require_verified_lift`; rejected nonfinite or invalid hold durations that could
  otherwise bypass a duration comparison.
- `skill/hardware.py`: reviewed and left unchanged. No register writes, new
  drivers, learned thresholds, scene descriptions, or targets were added.
- `tests/test_skill_safety.py`: synthetic tests cover stale/invalidation cases,
  intermediate effort loss with recovered endpoints, missing/delayed feedback,
  invalid bounds, a mock command owner's failure latch, and incomplete success
  evidence. The mock is not a physical controller or slip-prevention validation.
- `analysis/compare_runs.py` reproduces command counts and timing from the source
  logs. `cross_run_metrics.json` records markers, source line numbers, and hashes.
- `analysis/verify_retrospective.py` checks the exact transfer-file inventory,
  source structure, numeric literals, prohibited path/data signatures, tests,
  skill format, and whitespace. Its output is `validation.json`. Manual review
  of all three transfer files supplements these limited automated scans.

Only cleaned `skill/` may transfer. This report, metrics, scripts, audit, and tests
remain in Run 005. Original reports, execution records, and earlier commits are
preserved; the retrospective is recorded by a new commit.

## Sources and reproduction

- [Run 001 report](</home/robot-operator/Documents/ChatGPT/Run 001/run/REPORT.md>),
  [event log](</home/robot-operator/Documents/ChatGPT/Run 001/run/evidence/session.jsonl>),
  [summary](</home/robot-operator/Documents/ChatGPT/Run 001/run/summary.json>).
- [Run 002 report](</home/robot-operator/Documents/ChatGPT/Run 002/RUN_REPORT.md>),
  [command ledger](</home/robot-operator/Documents/ChatGPT/Run 002/evidence/DECISIONS.md>),
  [event log](</home/robot-operator/Documents/ChatGPT/Run 002/evidence/control.jsonl>),
  [initial lift](</home/robot-operator/Documents/ChatGPT/Run 002/evidence/initial_lift.json>),
  [extended lift](</home/robot-operator/Documents/ChatGPT/Run 002/evidence/clearance_lift.json>).
- [Run 003 report](</home/robot-operator/Documents/ChatGPT/Run 003/evidence/REPORT.md>),
  [event log](</home/robot-operator/Documents/ChatGPT/Run 003/evidence/session.jsonl>).
- [Run 004 report](</home/robot-operator/Documents/ChatGPT/Run 004/REPORT.md>),
  [event log](</home/robot-operator/Documents/ChatGPT/Run 004/evidence/session.jsonl>),
  [summary](</home/robot-operator/Documents/ChatGPT/Run 004/evidence/summary.json>),
  [retained controller](</home/robot-operator/Documents/ChatGPT/Run 004/evidence/controller.py>).
- [Run 005 report](</home/robot-operator/Documents/ChatGPT/Run 005/REPORT.md>),
  [event log](</home/robot-operator/Documents/ChatGPT/Run 005/evidence/control.jsonl>),
  [summary](</home/robot-operator/Documents/ChatGPT/Run 005/evidence/summary.json>),
  [retained controller](</home/robot-operator/Documents/ChatGPT/Run 005/runtime/control.py>).

From the Run 005 workspace, run `python3 -B analysis/compare_runs.py`, then
`python3 -B analysis/verify_retrospective.py`. These are offline operations.
