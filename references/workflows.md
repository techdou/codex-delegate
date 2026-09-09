# Codex delegation workflows

## Discover models before choosing a version

```bash
python scripts/run.py --list-models
python scripts/run.py --model-info <model-id>
python scripts/run.py --probe-model <model-id> --cwd .
```

Use this when the caller asks what Codex currently offers, asks for the newest/strongest available version, or names an unfamiliar model id. Do not answer those questions from a static list.

## Fast second opinion

```bash
python scripts/run.py --mode review --profile fast --cwd . --task "Review the patch for concrete correctness issues only."
```

## Deep review on an explicit model

```bash
python scripts/run.py --mode review --model <model-id> --profile deep --cwd . --task "Perform a deep architecture and correctness review."
```

## Exact reasoning effort

```bash
python scripts/run.py --mode ask --model <model-id> --reasoning-effort <advertised-effort> --cwd . --task "Analyze the tradeoffs."
```

## Review external material

```bash
python scripts/run.py --mode review --cwd . --input /path/to/material --task "Return prioritized findings."
```

## Edit a document

```bash
python scripts/run.py --mode edit --cwd . --input docs/source.md --task "Rewrite the document for a beginner audience and save the requested output."
```

## Coding worker

```bash
python scripts/run.py --mode agent --cwd . --task "Fix the failing tests, run the relevant suite, and report changed files plus validation."
```

## Continue the same Codex reviewer/writer

Use one stable opaque key for the parent Agent conversation:

```bash
python scripts/run.py --session auto --session-key <host-key> --mode review --cwd . --task "Review this project and identify the top issues."
python scripts/run.py --session auto --session-key <same-host-key> --mode review --cwd . --task "Continue: deeply analyze issue 2 and propose a fix."
```

The second call resumes the exact mapped Codex thread.

## Inspect cache/session diagnostics

```bash
python scripts/run.py --session auto --session-key <host-key> --cwd . \
  --task "Continue the analysis." --meta-output .codex-meta.json
python scripts/run.py --session-info --session-key <host-key> --cwd .
```

Use provider-reported `cached_input_tokens`; do not equate “resumed” with “cache hit”.

## Start an independent opinion

```bash
python scripts/run.py --session new --session-key <host-key> --mode review --cwd . --task "Review independently from scratch."
```
