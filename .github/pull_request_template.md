## Summary

Explain the user-visible behavior and why the change belongs in this pipeline.

## Verification

- [ ] A failing test demonstrated the missing/broken behavior before implementation.
- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] `mypy src`
- [ ] `pytest`
- [ ] `python -m build`
- [ ] `bash -n scripts/*.sh`

## Safety and compatibility

- [ ] Thai transcript quality gates are unchanged or strengthened.
- [ ] Low-confidence speech is preserved or explicitly review-gated.
- [ ] Source media, secrets, local paths, and generated artifacts are not committed.
- [ ] ChatCut remains an execution surface; Codex retains decision ownership.
- [ ] Canonical schema or skill changes include migration/documentation updates.

## Upstream attribution

Identify any code or design ported from `browser-use/video-use` or another project and confirm its license notice is retained.
