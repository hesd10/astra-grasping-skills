# Online motor-command decisions

One online motor-command decision for each submitted bounded command containing motor deltas. Includes probes, corrections, closures, lift segments and recovery; excludes read-only setup, image viewing, automatic servo steps, and operator-requested shutdown.

| Decision | UTC | Intended segment |
|---:|---|---|
| 1 | 00:42:01 | probe_shoulder |
| 2 | 00:42:27 | probe_wrist |
| 3 | 00:42:48 | probe_elbow |
| 4 | 00:43:11 | raise_clearance |
| 5 | 00:43:44 | align_pan_open |
| 6 | 00:44:17 | advance_open |
| 7 | 00:44:52 | approach_carton |
| 8 | 00:45:30 | reach_probe |
| 9 | 00:46:01 | insert_fingers |
| 10 | 00:46:35 | deepen_insertion |
| 11 | 00:47:10 | full_insertion |
| 12 | 00:47:41 | level_and_insert |
| 13 | 00:48:09 | seat_grasp |
| 14 | 00:48:45 | raise_contact_height |
| 15 | 00:49:19 | gentle_close |
| 16 | 00:49:40 | secure_contact |
| 17 | 00:50:26 | initial_lift |
| 18 | 00:50:55 | clearance_lift |
| 19 | 00:51:46 | recovery_open |
| 20 | 00:52:13 | lower_around_carton |
| 21 | 00:52:42 | center_regrasp |
| 22 | 00:53:11 | regrasp_close |
| 23 | 00:53:34 | regrasp_preload |
| 24 | 00:54:00 | confirm_preload |
| 25 | 00:54:35 | deeper_side_contact |
| 26 | 00:55:10 | clear_fixed_finger |
| 27 | 00:55:52 | firm_regrasp |
| 28 | 00:56:41 | clear_upper_edges |
| 29 | 00:56:58 | wide_clearance |
| 30 | 00:57:23 | descend_beside |
| 31 | 00:57:52 | center_broad_face |
| 32 | 00:58:17 | withdraw_clear |
| 33 | 00:58:52 | lift_gripper_clear |
| 34 | 00:59:51 | align_above_carton |
| 35 | 01:00:18 | clear_moving_finger |

Labels describe intent only. They do not certify enclosure, clearance, or success.

Decisions 1–3: isolated probes. Decisions 4–14: approach and alignment. Decisions 15–16: initial closure. Decisions 17–18: lift segments; the carton slipped during the second segment. Decisions 19–35: recovery, regrasp, and clearance corrections; none produced a verified stable lift.

Read-only startup and the operator-requested stop/torque release are documented separately and are not included in the 35-command count. No automatic hardware-fault stop or online thermal-diagnostic pause occurred.
