---
name: codex-delegate
description: Delegate bounded work to the locally installed OpenAI Codex CLI, including model discovery/selection, reasoning control, session continuity, cache-aware repeated review/writing, workspace-scoped coding, and explicit Skill health/update/rollback maintenance. Use only when the user or parent agent explicitly asks for Codex/Codex CLI/OpenAI Codex, asks about Codex models or reasoning, or asks to continue/resume a prior Codex delegation. Do not activate for generic writing, review, analysis, or coding that does not request Codex.
---

# Codex CLI delegation

Use the local Codex CLI as a delegated worker. The parent agent owns routing, authorization, verification, session affinity, and the final user-facing answer.

## Preserve continuity when the task continues

For related Codex turns in the same parent-agent conversation, prefer managed session affinity instead of starting a fresh CLI thread each time:

```bash
python3 <skill-dir>/scripts/run.py \
  --session auto \
  --session-key <stable-opaque-host-session-key> \
  --mode <ask|review|edit|agent> \
  --cwd <workspace> \
  --task "<bounded task>"
```

Generate/reuse one opaque `--session-key` for the parent conversation, or rely on `CODEX_SKILL_SESSION_KEY` / `FOREIGN_MODEL_SESSION_KEY` when the host provides one. The local mapping is scoped by provider + workspace + session key, so different workspaces do not share a Codex thread.

Session policy:

- `auto`: resume the mapped Codex thread when present; otherwise create and record one.
- `continue`: require an existing mapping; fail rather than silently starting over.
- `new`: intentionally create a fresh native thread and replace the mapping for this host-session/workspace.
- `off`: one-shot behavior; use for unrelated work that does not need continuity.

Do not use `resume latest` as automatic affinity. `--resume` remains available only for explicit/manual recovery. Managed resume verifies the actual `thread.started` id and fails closed on a mismatch.

Use `--session-info`, `--list-sessions`, and `--forget-session` to inspect/delete wrapper mappings. The registry stores session metadata, workspace path, model/cache stats, and hashed host key only; it does not store task text or answers.

## Keep provider cache-friendly

Managed continuation preserves Codex-native conversation history and usually gives the provider the best opportunity to reuse cached input. The wrapper also keeps invariant delegation instructions before the changing task text to maximize stable prompt prefixes.

When cache behavior matters, add:

```bash
--meta-output .codex-run-meta.json
```

Inspect `cache.cached_input_tokens`, `cache.hit_ratio`, and `cache_affinity`. Do not claim a cache hit without provider-reported usage. The wrapper intentionally does **not** memoize final answers because workspace/document state may change.

## Maintain the Skill explicitly, never during ordinary delegation

Normal `ask/review/edit/agent` runs must not check the network for Skill updates. For health, compatibility, or upgrade requests use the maintenance interface instead:

```bash
python3 <skill-dir>/scripts/run.py --doctor
python3 <skill-dir>/scripts/run.py --update-info
python3 <skill-dir>/scripts/run.py --check-update [--manifest <source>]
```

Only run `--self-update` or `--rollback` when the user/parent explicitly authorizes changing the installed Skill. Both require the second opt-in `--allow-self-update`. The updater requires a trusted manifest, HTTPS for remote sources, SHA-256 verification, safe ZIP extraction, candidate validation, a pre-replacement runtime smoke check, and a local backup. It never upgrades the provider CLI itself.

Read [references/maintenance.md](references/maintenance.md) before publishing an update manifest or changing installed Skill files.

## Handle model questions first

For models, versions, or reasoning settings, query the wrapper rather than hard-coding a list:

```bash
python3 <skill-dir>/scripts/run.py --list-models
python3 <skill-dir>/scripts/run.py --model-info <model-id>
python3 <skill-dir>/scripts/run.py --current-model
python3 <skill-dir>/scripts/run.py --probe-model <model-id> --cwd <workspace>
```

Use `--model <id>` for an exact version. Use `--reasoning-effort <advertised-value>` for exact control or `--profile fast|balanced|deep` for intent-level control. `deep` should use the highest advertised reasoning level when resolvable; never hard-code future effort names.

## Select the least-privileged work mode

- `ask`: answer/write/analyze without changing files.
- `review`: inspect material/project and return findings without changes.
- `edit`: create/modify authorized workspace files without requiring a full command loop.
- `agent`: modify files and run relevant commands/tests/builds inside `workspace-write` sandbox.
- `unsafe`: broad host access only when explicitly requested on an already isolated host; never use it merely to bypass a permission failure.

Use repeatable `--input <path>` and `--task-file <file>` for long instructions. In `edit`/`agent`, external inputs outside `--cwd` require explicit `--extra-dir` authorization or must be copied into the workspace.

## Delegation and verification rules

- Give the child the bounded task, constraints, desired output, and acceptance criteria; remove routing phrases such as “ask Codex to”.
- Reuse a managed session only when the new turn is genuinely part of the same goal. Start `new` for an unrelated task to avoid context contamination.
- Keep credentials, tokens, private keys, and secrets out of prompts and artifacts.
- Treat non-zero wrapper exit codes as failure. Retry once only for a concrete safe fix.
- For `edit`/`agent`, inspect the requested output or workspace diff before claiming success.
- Do not recursively call the Codex skill from the delegated Codex worker.
- Do not escalate to `unsafe` because sandbox/approval blocked an action.

Read [references/maintenance.md](references/maintenance.md) for self-maintenance, [references/session-cache.md](references/session-cache.md) for continuity/cache behavior, [references/model-control.md](references/model-control.md) for model discovery/profiles, [references/security.md](references/security.md) before changing permissions, [references/official-cli.md](references/official-cli.md) for CLI compatibility, and [references/workflows.md](references/workflows.md) for examples.
