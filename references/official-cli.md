# Codex CLI compatibility notes

Verified against current OpenAI Codex CLI documentation/repository behavior on 2026-09-04. Use this file when diagnosing CLI behavior or updating wrapper flags.

Official references:

- CLI reference: https://developers.openai.com/codex/cli/reference
- Codex repository CLI source: https://github.com/openai/codex
- App-server model schema: https://github.com/openai/codex/blob/main/codex-rs/app-server-protocol/schema/json/v2/ModelListResponse.json

## Non-interactive contract

Use `codex exec` for headless delegation. The wrapper combines:

```text
--json
--output-last-message <temporary-file>
-C <workspace>
--sandbox <policy>
--ask-for-approval never
```

The output-last-message file is the primary final-result channel; JSONL is retained for diagnostics/raw capture and as a compatibility fallback.

## Model discovery and selection

Current Codex builds expose:

```bash
codex debug models
codex debug models --bundled
```

`debug models` refreshes/reads the runtime model catalog and emits JSON. The catalog can advertise model ids, display names, reasoning levels, visibility, input modality and other model metadata. The wrapper normalizes this through `--list-models` and `--model-info`.

`--model MODEL` selects the model for `codex exec`.

Reasoning is configured through `model_reasoning_effort`. The wrapper passes it as a one-run config override rather than maintaining a fixed enum because the model catalog can advertise new effort names over time.

Catalog membership is not treated as a hard entitlement guarantee. Wrapper `--probe-model MODEL` performs a tiny read-only ephemeral execution when actual account/runtime usability must be verified.

## Permission mapping

```text
ask/review -> --sandbox read-only
edit/agent -> --sandbox workspace-write
unsafe     -> --sandbox danger-full-access
```

`--add-dir <path>` grants an additional writable root alongside the main workspace. It is an authorization boundary, not merely a context flag.

The wrapper automatically adds an external input directory only in `ask`/`review`, where the sandbox remains read-only. In `edit`/`agent`, external inputs outside `--cwd` require explicit `--extra-dir` authorization.

## Session and usage behavior

Codex persists native threads under the user's Codex home and supports resuming them. The wrapper's managed session layer records the exact `thread.started.thread_id` and later calls `exec resume <id>` instead of selecting an ambiguous latest session. A resumed run is verified against the thread id emitted by JSONL.

`turn.completed.usage` can include `input_tokens`, `cached_input_tokens`, and `output_tokens`. The wrapper surfaces these only as diagnostics; native prompt caching remains owned by Codex/OpenAI.

## Optional controls

- `--search` enables Codex live web search for runs that actually need current web information.
- `--output-schema <schema.json>` constrains final structured output.
- `--ephemeral` avoids persisting rollout/session files and is therefore incompatible with managed session continuity.
- manual `exec resume` remains available through wrapper `--resume`; managed continuity should prefer exact saved ids.

Keep authentication material out of prompts, logs, repositories, and generated artifacts.

## v1.4 maintenance compatibility note (2026-09-04)

Current Codex 0.152.x builds expose `codex doctor --json`; the wrapper uses it only as an optional redacted local diagnostic summary. Skill update checks do not depend on Codex's own update cache because update probes can fail independently of runtime health.

The OpenAI repository currently supports the standalone installer (including Windows), npm `@openai/codex`, Homebrew, and release binaries. The Skill never runs a package-manager or standalone CLI updater automatically. `skill.json` records the CLI version through which this Skill's protocol assumptions were reviewed, while `--doctor` performs local capability checks so compatibility is not decided by a version string alone.
