# Third-person phone video

Six 12x muted H.264 previews, 720 x 1280 portrait, are included in Git. Seven originals were copied from an HBN AL80 phone and verified locally. Original files are not distributed in this Git repository; original audio remains only in those local files.

| Run | Recorded source duration | Preview duration | Preview |
|---|---:|---:|---|
| 001 | 20:47 | 1:47 | [Video](previews/run-001-12x-muted.mp4) |
| 002 | 18:38 | 1:33 | [Video](previews/run-002-12x-muted.mp4) |
| 003 | 12:57 | 1:05 | [Video](previews/run-003-12x-muted.mp4) |
| 004 | 17:23 | 1:27 | [Video](previews/run-004-12x-muted.mp4) |
| 005 | 11:34 | 0:58 | [Video](previews/run-005-12x-muted.mp4) |
| 006 | 12:00 | 1:00 | [Video](previews/run-006-12x-muted.mp4) |

Attempt 001 joins two recordings separated by a several-minute gap. A three-second title card marks the gap; no missing frames are reconstructed. Other attempts have one source recording each. These durations are not task execution times, and phone timestamps are not precisely aligned with robot logs. Third-person footage is not an agent input.

The [manifest](manifest.json) records original filenames, hashes, byte sizes, mapping and processing details. Previews use HLG HDR to BT.709 SDR conversion, timestamp scaling and frame sampling, without generated interpolation. Full decode, duration and absence of audio were checked. Historical embedded title cards retain their original wording.

To rebuild with locally available originals, place them under `physical/videos/originals/` and run `python3 physical/scripts/process_videos.py`. FFmpeg needs libx264, libass, zscale and tonemap. The recorded encoder version was 7.0.2; `FFMPEG_BINARY` can select it.
