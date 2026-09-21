# From Grasping to Skills

**A six-attempt Astra/XLeRobot case study of cross-session skill reuse.**

We conducted six successive carton-grasping trials with Astra and a real XLeRobot. The task was to grasp an empty milk carton and hold it stably clear of the desk. Each attempt begins in a fresh workspace and conversation; only reviewed general procedures and reusable code in `skill/` carry experience forward. Model weights are not updated.

This repository documents what was learned, what was actually implemented, and how verification and recovery changed across the sequence. It preserves the observations, control programs, skill updates and operator interventions across all six attempts.

## Results

| Attempt | Outcome | Execution time | Model requests | Motion commands |
|---|---|---:|---:|---:|
| 001 | Success | 31:39 | 110 | 31 |
| 002 | Failure | 24:24 | 82 | 35 |
| 003 | Failure | 19:31 | 65 | 25 |
| 004 | Success | 26:35 | 85 | 31 |
| 005 | Success | 18:51 | 65 | 25 |
| 006 | Success | 18:45 | 54 | 31 |

The early outcomes need to be read alongside the grasping process. Run 001 succeeded partly through favorable circumstances: its initial shallow grasp rotated the carton, but left it in a pose that still allowed regrasping. Its premature success judgment also required an operator correction before the final lift. Runs 002 and 003 exposed weaknesses that this first success had not resolved: shallow contact and larger rotations left the carton in poses from which recovery failed, and a successful test lift did not guarantee retention during further lifting. These failures informed stronger enclosure checks, renewed verification and recovery procedures. Runs 004–006 subsequently achieved more stable grasps; 004 and 006 detected instability and rebuilt the grasp under desk support before continuing. See the [per-attempt analysis](physical/report/REPORT.md#43-each-attempt-and-its-skill-updates) for the observations and corresponding skill changes.

Among successful attempts, execution time declined from 31:39 to 18:45 (40.8%), and recorded model requests from 110 to 54 (50.9%). Logs show reuse of grasp verification and support-restoration procedures. These observations associate skill accumulation with improved execution in this sequence; one attempt per evolving version, human interventions and an additional pre-sixth-attempt retrospective prevent a controlled causal claim of stable improvement.

Execution time includes preparation, coding, observations, actions, waiting and recovery, and excludes subsequent reporting and skill closeout. Failure time is time to termination, not faster successful completion. Success denotes visible stable suspension; the requested 3 cm clearance was not independently measured. See the measurement definitions for exact endpoints and counting rules.

## Read the study

- [Full report](physical/report/REPORT.md)
- [Six-attempt index](physical/runs/README.md) and [video previews](physical/videos/README.md)
- [Data guide](physical/DATA_GUIDE.md)
- [Measurement definitions](physical/analysis/METHODOLOGY.md) and [token accounting](physical/analysis/TOKEN_REPORT.md)
- [Machine-readable results](results.json)

`physical/` contains original workspaces, camera frames, telemetry, visible-message exports, skill versions and video previews, alongside reports and navigation. Historical evidence retains its recorded wording except for documented personal-path redactions. Original and distributed hashes are retained for modified source files. Large phone originals are local-only; manifests and hashes document them.

## Offline verification

```bash
python3 scripts/verify_repository.py
```

Verification checks source-file integrity, the six-attempt result table and local documentation links. It does not contact a model or robot. Archived motor controllers are research evidence, not an unattended hardware reproduction shortcut.

## Repository scope

This repository is dedicated to the real-robot carton-grasping case study. Its repository history starts with one consolidated root commit. Historical commit identifiers inside the evidence describe the original experimental record, not the consolidated repository history.
