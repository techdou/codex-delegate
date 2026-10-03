---
name: codex-delegate
description: Delegate bounded work (coding, code review, analysis, writing, debugging) to the locally installed OpenAI Codex CLI as a sub-worker — model discovery/selection, reasoning control, session continuity, cache-aware repeated runs, sandboxed workspace edits. Use only when the user or parent agent explicitly asks for Codex/Codex CLI/OpenAI Codex, asks about Codex models or reasoning, or asks to continue/resume a prior Codex delegation. Do not activate for generic coding, review, analysis, or writing tasks that do not name Codex.
license: MIT
compatibility: Requires the OpenAI Codex CLI (npm i -g @openai/codex, logged in) and Python 3.10+. Works on Windows, macOS, and Linux.
metadata:
  version: "1.4.3"
---

# Codex CLI delegation

Use the local Codex CLI as a delegated worker. The parent agent owns routing, authorization, verification, session affinity, and the final user-facing answer.

## Quick reference

Minimal one-shot delegation (no session management):

```bash
python3 <skill-dir>/scripts/run.py \
  --mode <ask|review|edit|agent> \
  --cwd <workspace> \
  --task "<bounded task>"
```

Mode picker:

- `ask` — answer/analyze/write without touching files (read-only sandbox)
- `review` — inspect a project/material and return findings, no changes (read-only)
- `edit` — create/modify authorized workspace files (no command loop)
- `agent` — edit files AND run relevant commands/tests/builds (workspace-write sandbox)
- `unsafe` — broad host access, only on explicit request; never use it to bypass a permission failure

Frequent switches: `--timeout <seconds>` (integer; default 1800, budget minutes as seconds), `--no-mcp` (skip all MCP servers — faster start, no handshake noise), `--model <id>`, `--profile fast|balanced|deep`, `--input <path>` (repeatable), `--task-file <file>`, `--dry-run` (print assembled command only).

Platform note: on hosts without a `python3` alias (common on Windows), invoke the same script with `python` — everything else is identical.

## Select the least-privileged work mode

Pick from the mode list above. In `edit`/`agent`, external inputs outside `--cwd` require explicit `--extra-dir` authorization or must be copied into the workspace. Do not escalate to `unsafe` because sandbox/approval blocked an action; use the controlled network switches below instead.

## Skip MCP servers on demand

Pass `--no-mcp` when the task needs no MCP tools (pure coding/review/writing). It forwards `-c mcp_servers={}`: Codex starts faster, no MCP handshake noise, and the run is immune to individual server startup failures. Session/cache metadata is unaffected. Default (flag off) keeps all configured MCP servers.

```bash
python3 <skill-dir>/scripts/run.py --no-mcp --mode ask --cwd <workspace> --task "<bounded task>"
```

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

## Handle model questions first

For models, versions, or reasoning settings, query the wrapper rather than hard-coding a list:

```bash
python3 <skill-dir>/scripts/run.py --list-models
python3 <skill-dir>/scripts/run.py --model-info <model-id>
python3 <skill-dir>/scripts/run.py --current-model
python3 <skill-dir>/scripts/run.py --probe-model <model-id> --cwd <workspace>
```

Use `--model <id>` for an exact version. Use `--reasoning-effort <advertised-value>` for exact control or `--profile fast|balanced|deep` for intent-level control. `deep` should be the highest advertised reasoning level when resolvable; never hard-code future effort names.

## Network access (measured 2026-09-17)

`agent` mode's `workspace-write` sandbox **blocks outbound sockets from delegated processes by default** — any HTTP API call the task itself makes (image generation, translation, REST relays) fails, typically surfacing WinError 10013 "socket access not permitted" on Windows. Codex's built-in web search is a separate axis: `--search` switches it from cached to live and does not require sandbox network. The two switches are **independent and orthogonal** — enable each that the task needs, and both if it needs both:

- `--search` — the agent needs live web search. Mounts Codex's built-in search tool; does not unblock subprocess sockets.
- `--network-access` — delegated scripts/processes must make outbound HTTP or socket calls. Passes `sandbox_workspace_write.network_access=true` through the native `--config` mechanism; the **file sandbox stays on**. This is a controlled switch, not an escalation.
- Split-run mode — when giving the worker outbound network is inappropriate, split the work: have the delegated worker produce the artifact it can offline (prompt file, plan, data file), and run the network call yourself in the parent agent's channel, writing outputs into the worker's directory. Keep the primary task logic on the worker's side so the delegation boundary stays clean.

Scope and persistence: `--network-access` applies to `edit`/`agent` modes only (the wrapper rejects it for read-only `ask`/`review`). The config travels on the command line, not in the session record — pass the flag again on every resumed (`-c` / managed session) call that still needs network.

## Measured pitfalls

- `--timeout` is **seconds**, an integer. `35m` fails argparse; `35` means 35 seconds and kills mid-task. Budget minutes as `--timeout 2100`.
- Codex refuses to run in a directory that is not inside a git repository ("Not inside a trusted directory"). Check with `git rev-parse --is-inside-work-tree` first; only run `git init` in the target workspace when it is inside no repo — never nest a new `.git` under an existing one.
- On Windows (v1.4.1+), the wrapper binds the whole child process tree to a kill-on-close Job Object: if the wrapper itself is killed by an outer timeout, the OS reaps the entire codex/MCP tree — no orphaned `codex.exe` or npx MCP processes. Timeout budgeting still matters; the tree cleanup is a safety net, not a reason to set tight timeouts.

## Delegation and verification rules

- Give the child the bounded task, constraints, desired output, and acceptance criteria; remove routing phrases such as “ask Codex to”.
- Reuse a managed session only when the new turn is genuinely part of the same goal. Start `new` for an unrelated task to avoid context contamination.
- Keep credentials, tokens, private keys, and secrets out of prompts and artifacts.
- Treat non-zero wrapper exit codes as failure. Retry once only for a concrete safe fix.
- For `edit`/`agent`, inspect the requested output or workspace diff before claiming success.
- Do not recursively call the Codex skill from the delegated Codex worker.

## Maintain the Skill explicitly, never during ordinary delegation

Normal `ask/review/edit/agent` runs must not check the network for Skill updates. For health, compatibility, or upgrade requests use the maintenance interface instead:

```bash
python3 <skill-dir>/scripts/run.py --doctor
python3 <skill-dir>/scripts/run.py --update-info
python3 <skill-dir>/scripts/run.py --check-update [--manifest <source>]
```

Only run `--self-update` or `--rollback` when the user/parent explicitly authorizes changing the installed Skill. Both require the second opt-in `--allow-self-update`. The updater requires a trusted manifest, HTTPS for remote sources, SHA-256 verification, safe ZIP extraction, candidate validation, a pre-replacement runtime smoke check, and a local backup. It never upgrades the provider CLI itself.

Read [references/maintenance.md](references/maintenance.md) before publishing an update manifest or changing installed Skill files, [references/session-cache.md](references/session-cache.md) for continuity/cache behavior, [references/model-control.md](references/model-control.md) for model discovery/profiles, [references/security.md](references/security.md) before changing permissions, [references/official-cli.md](references/official-cli.md) for CLI compatibility, and [references/workflows.md](references/workflows.md) for examples.
