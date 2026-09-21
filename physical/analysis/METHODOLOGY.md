# Measurement definitions: fixed-base grasping

Success is stable visible suspension of the entire carton. Attempts 001, 004, 005 and 006 succeeded; 002 and 003 failed. The withdrawn first declaration in 001 is not the final outcome. The later prompt's 3 cm request was not independently measured and is not the common classification threshold.

## Execution interval

The start is the first archived `task_started` event. Successful endpoints are 001's final corrected snapshot, 004's last `kind=final` event (line 2146, fractional seconds retained), 005's `control_end_utc`, and 006's `monitoring_end_utc`. Failure endpoints are 002's `torque_release_utc` and 003's `torque-release.json` time. Preparation, coding, motion, observations, waits and recovery are included. Reporting and skill closeout after these endpoints are excluded. An interrupted and resumed attempt keeps its original start.

The endpoints are execution markers, not identical measurements of first physical lift. Software monitoring ending does not imply torque was disabled. The measurement adjustment moves the common start approximately 9–15 seconds earlier than some original run reports; it does not rewrite the evidence.

| Run | Outcome | Execution time | Model requests | Motion commands |
|---|---|---:|---:|---:|
| run-001 | Success | 31:39 | 110 | 31 |
| run-002 | Failure | 24:24 | 82 | 35 |
| run-003 | Failure | 19:31 | 65 | 25 |
| run-004 | Success | 26:35 | 85 | 31 |
| run-005 | Success | 18:51 | 65 | 25 |
| run-006 | Success | 18:45 | 54 | 31 |

The model-request count is the number of unique `response_id` values with a `token_usage_record` written within the interval. Requests whose usage arrived after the endpoint and interrupted requests with no usage are not counted. The count covers observations and programming, not just robot commands.

## Motion submissions

One bounded joint/gripper command counts once even if several joints move. Blocked/incomplete submissions count; servo interpolation samples do not. Per-run selectors are: 001 `motion_start`/`grip_start`; 002 `command` with nonempty `data.delta`; 003 `online_command` with nonempty `command.delta`; 004 `command` with `data.op=move`; 005 `decision` with `command.op=move`; 006 `motion_start`.

The original controller-specific grouping counts (29, 35, 24, 36, 30, 39) included observations and service operations differently. They are not a common interaction count. Full-workflow model requests are 117, 89, 72, 90, 69 and 58, including closeout; do not mix them with the execution table.

## Token scope and provenance

Full-workflow token totals include initial execution, correction/resumption, failure termination, reporting and the final skill audit/commit. Separate post-task torque release, questions and cross-run retrospective are excluded. Attempts 002/003 contain termination and reporting within the same closing turn. Usage is deduplicated by response ID; cached input and reasoning output are subsets, not additional quantities. Attempt 003 spans two source logs; attempt 005 contains compaction, so the last cumulative snapshot alone is insufficient. This is a log audit, not a billing statement.

The operator removed software temperature alarms in every attempt. Exact intervention timing and diffs are incomplete, and no unmeasured correction cost is subtracted.

Exact endpoints, file paths, line numbers and request IDs are in [execution_metrics.json](execution_metrics.json). From the repository root run `python3 physical/scripts/recompute_execution_metrics.py` and `python3 physical/scripts/recompute_metrics.py`. These are offline operations; they regenerate derived JSON without contacting the robot or model.
