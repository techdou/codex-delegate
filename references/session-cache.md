# Codex session continuity and cache behavior

## Why managed affinity exists

A parent Agent conversation and a Codex CLI thread are separate state machines. Repeatedly starting `codex exec` creates new native threads unless a prior thread is resumed. `--session auto` bridges them using a local mapping:

```text
provider + resolved workspace + opaque host-session key -> Codex thread id
```

The raw host key is never persisted. Its hash is used to locate the record.

Default local state location:

- macOS/Linux: `$XDG_STATE_HOME/foreign-cli-skills/` or `~/.local/state/foreign-cli-skills/`
- Windows: `%LOCALAPPDATA%/foreign-cli-skills/state/`
- override: `FOREIGN_CLI_SKILL_STATE_DIR`

Records contain the native thread id, workspace, turn count, model/profile metadata, last cache/usage stats, timestamps, and a hashed session key. They do not contain prompts or responses.

## Policies

```text
off       no managed mapping
auto      resume mapped id or create a new native thread
continue  mapped id must exist; otherwise fail
new       do not resume; create fresh thread and replace mapping
```

Manual `--resume` is kept for operator-directed recovery but cannot be mixed with managed `--session`.

Managed resume uses an exact saved thread id rather than `--last`. After execution the wrapper checks the `thread.started.thread_id`. If it differs from the requested mapped id, the wrapper returns an error instead of silently accepting a fresh thread.

A small local lease file prevents two wrapper processes from concurrently using the same managed session. A live conflicting process results in a fail-fast “session already in use” error.

## Cache behavior

Codex `exec --json` can report usage containing:

```json
{
  "input_tokens": 10000,
  "cached_input_tokens": 8000,
  "output_tokens": 500
}
```

The wrapper computes `cached_input_tokens / input_tokens` as a diagnostic hit ratio and stores the latest metrics in the session record. Use `--meta-output <file>` to capture per-run metadata inside the workspace.

A resumed thread often provides better native continuity and cache reuse than unrelated fresh one-shot executions, but a resume is not itself proof of a cache hit. Only provider-reported cached token counts are evidence.

The prompt is deliberately ordered as:

1. invariant delegated-worker context;
2. invariant mode/permission contract;
3. relatively stable input paths;
4. variable per-turn task.

This preserves a longer stable prefix between related calls.

## No response memoization

The wrapper intentionally does not cache final model answers. Files, repository state, external inputs, and instructions can change between calls, so replaying a prior answer could be stale or unsafe.

## When to rotate

Use the same managed thread for follow-ups on the same review, document, or coding goal. Use `--session new` when switching to an unrelated topic, when old context is actively harmful, or when the caller explicitly asks for a fresh independent opinion.

Changing models inside one continuing thread may preserve conversational history but can reduce provider cache affinity. Prefer a fresh session for independent cross-model benchmarking; preserve the session for genuine conversational continuity.
