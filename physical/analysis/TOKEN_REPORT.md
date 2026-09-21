# Token usage audit for six physical attempts

Values are derived from logged per-request usage, not estimated from text length. The workflow includes execution, recovery, termination, reporting and skill audit/commit. Separate later torque release, questions and retrospective work are excluded from the main totals.

| Run | Input including cache | Cached input subset | Output including reasoning | Total | Workflow requests |
|---|---:|---:|---:|---:|---:|
| 001 | 12,981,976 | 12,689,408 | 44,538 | 13,026,514 | 117 |
| 002 | 8,746,427 | 8,531,712 | 38,733 | 8,785,160 | 89 |
| 003 | 6,983,492 | 6,794,368 | 26,760 | 7,010,252 | 72 |
| 004 | 9,867,833 | 9,702,784 | 38,418 | 9,906,251 | 90 |
| 005 | 6,082,485 | 5,954,816 | 25,717 | 6,108,202 | 69 |
| 006 | 5,737,020 | 5,570,944 | 30,295 | 5,767,315 | 58 |
| Total | 50,399,233 | 49,244,032 | 204,461 | 50,603,694 | 495 |

Repeated context is included on each request. Cached input is part of input; reasoning output is part of output. Neither is added twice. Noncached input totals 1,155,201 and reasoning output 101,142 tokens. No subscription quota or monetary cost is inferred.

| Run | Experiment workflow | Later release/questions/retrospective | Entire session |
|---|---:|---:|---:|
| 001 | 13,026,514 | 574,606 | 13,601,120 |
| 002 | 8,785,160 | 0 | 8,785,160 |
| 003 | 7,010,252 | 0 | 7,010,252 |
| 004 | 9,906,251 | 527,646 | 10,433,897 |
| 005 | 6,108,202 | 6,328,884 | 12,437,086 |
| 006 | 5,767,315 | 496,644 | 6,263,959 |

The entire-session total is 58,531,474. The dedicated retrospective after 005 used 2,265,327 tokens, distinct from earlier questions about skills/results. It is not charged to execution in 005 or hidden inside 006's execution measure.

Usage is deduplicated by response ID and checked against final thread totals. Attempt 003 combines two logs for the same task; attempt 005 contains compaction. Cumulative token snapshots must not be summed or added to per-request usage. Every record checks total = input + output. Interrupted requests without usage cannot be quantified, so this is not a billing audit.

[Request-level source records](token_usage.json) retain identifiers, line numbers, hashes and turn boundaries. `python3 physical/scripts/recompute_metrics.py` operates on the repository export. The historical `count_tokens_original.py` instead expects the originating machine's logs and is retained as source documentation.
