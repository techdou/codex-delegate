# Codex model discovery and reasoning control

## Discovery contract

The wrapper uses the installed CLI's `codex debug models` command. Current Codex builds refresh the model catalog by default; `--bundled-models` asks for the catalog shipped with the local binary instead.

Commands:

```bash
python scripts/run.py --list-models
python scripts/run.py --model-info <model-id>
python scripts/run.py --current-model
python scripts/run.py --probe-model <model-id> --cwd <workspace>
```

`--list-models` normalizes both the raw `debug models` shape and app-server-style model metadata when present. Important fields include model id/display name, visibility, default reasoning effort, supported reasoning efforts, input modalities, model specialty, multi-agent version, and service tiers when advertised.

A catalog entry is evidence that the CLI knows about a model, not a guarantee of account entitlement. Use `--probe-model` when actual usability must be confirmed.

## Selection

Use an exact catalog id:

```bash
python scripts/run.py --model <model-id> --task "..."
```

Do not hard-code a static list in prompts or documentation; Codex model catalogs and supported reasoning levels change independently of this skill.

## Reasoning control

Exact control:

```bash
--reasoning-effort <advertised-value>
```

The wrapper intentionally does not use an argparse enum. When model metadata can be resolved, it validates the requested effort against that model's advertised values. This allows newer efforts such as `max`, `ultra`, or future provider-defined names without a skill release.

Intent profiles:

```text
fast     -> lowest recognized effort advertised by the selected/current model
balanced -> model's advertised default reasoning effort when available
deep     -> highest recognized effort advertised by the selected/current model
```

If a dry run or older CLI cannot resolve metadata, `fast` conservatively falls back to `low`, `deep` to `high`, and `balanced` leaves the CLI default unchanged. Explicit `--reasoning-effort` always takes precedence over `--profile`.

Profiles do not guess a "strongest" model family. Pair a concrete `--model` with a profile when model version matters.
