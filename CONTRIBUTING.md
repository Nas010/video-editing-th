# Contributing

## Development setup

```bash
git clone https://github.com/Nas010/video-editing-th.git
cd video-editing-th
scripts/setup_macos.sh     # or scripts/setup_debian.sh
```

Create a feature branch. Keep source footage, asset libraries, model weights, database files, renders, credentials, and personal paths outside Git.

## Required workflow

1. Add a failing test for each behavior change.
2. Implement the smallest change that passes it.
3. Run:

```bash
ruff check .
ruff format --check .
mypy src
pytest
python -m build
bash -n scripts/*.sh
```

4. Update documentation and schema/version notes when an external contract changes.
5. Include exact verification evidence in the pull request.

## Safety invariants

Changes must not weaken the Thai quality gate, cut through known word intervals, delete low-confidence speech silently, delegate decisions to ChatCut AI, overwrite source media, expose secrets, or import an entire private asset library into ChatCut.

## Pull requests

Keep commits focused and describe upstream-derived changes explicitly. Any change to the Codex skill requires static skill-contract tests and pressure-scenario coverage. Behavioral skill evaluation should be run in a Codex environment with multi-agent support when available.
