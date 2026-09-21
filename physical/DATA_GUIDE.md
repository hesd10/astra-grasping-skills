# Physical evidence guide

Open a run README, follow the keyframes to original images, and compare the controller, action log and telemetry in `workspace/`. Conversations provide visible user/assistant messages, selected tool events and usage records. They retain historical content rather than being rewritten to match the current interpretation, with documented personal-path anonymization.

`provenance/source-files.json` records the original source path, archived relative path, byte size and SHA-256 for copied workspace files. `.git`, caches, lock files and symlinks were excluded. `commits.txt` records original commit IDs; `skill-snapshots/<commit>/` preserves skill-changing versions. Attempt 005 includes its ordinary output and later retrospective revision. An output snapshot alone is not independent proof of the following attempt's exact input.

The export excludes system/developer messages, private reasoning, compaction internals, tool catalogs and non-text payloads. `export-notes.json` describes the filtering; session source identifiers and hashes retain provenance. Truncated original tool results remain truncated. Saved images are separate from message payloads and are not asserted to be byte-identical to every transmitted payload.

There are 687 saved camera images. `IMAGES.md` indexes all retained files; `image-observations.json` indexes explicit image-view calls. Capture does not imply viewing. `analysis/keyframes.json` maps 27 selected panels to original paths and hashes. A filename overwritten during execution has only its retained final contents.

The six muted 12x phone-video previews are in Git. Seven large originals are local-only and are intentionally absent from a Git clone; the manifest retains their hashes. Attempt 001 has a visibly marked recording gap, and phone timestamps are not precisely synchronized with robot logs. [Video details](videos/README.md).

The module root changed to `physical/`, but paths inside its provenance and scripts remain relative to that module. Personal home-directory prefixes in historical absolute paths are anonymized. Reader-facing navigation is relative and portable. Offline verification skips unavailable local-only originals while explicitly reporting that limitation.

## Public-copy redactions

[Redaction manifest](provenance/public-redactions.json) records each path-only transformation, original and distributed hashes and sizes. In `source-files.json`, `sha256` and `size` verify the distributed copy; `original_sha256` and `original_size`, when present, identify the untouched local original. Files without those fields remain byte-identical to the original archive. Camera images, telemetry values, outcomes and historical prompt instructions are not rewritten.

See the [experimental record inventory](analysis/RECORD_INVENTORY.md) for configuration evidence and historical details that are not recoverable from the retained records.
