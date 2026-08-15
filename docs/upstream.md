# Upstream Relationship

This repository is a specialized derivative of [`browser-use/video-use`](https://github.com/browser-use/video-use), reconstructed from upstream commit:

```text
92c2b34e44c205cbc2acae7f6ca7c1c219d5dd66
```

The target repository already existed, so GitHub could not convert it into a platform-level fork. Attribution is retained in `NOTICE`, `THIRD_PARTY.md`, and the commit history in this repository.

For local comparison with later upstream work:

```bash
git remote add upstream https://github.com/browser-use/video-use.git
git fetch upstream
```

Do not merge upstream automatically. This project intentionally replaces the original provider-specific transcription path and general-purpose editing assumptions with Thai quality gates, canonical plans, persistent asset retrieval, and Codex-controlled ChatCut execution. Review upstream changes by component and port useful fixes with tests.
