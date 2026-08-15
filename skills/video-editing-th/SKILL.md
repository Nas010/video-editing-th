---
name: video-editing-th
description: Use when turning raw Thai talking-head footage into a reviewed edit with retake removal, Thai captions, local asset selection, and Codex-controlled ChatCut timeline execution.
---

# Thai Video Editing

## Principle

Codex makes every editorial and creative decision. ChatCut is an editable NLE execution surface, not the decision-maker. **Never delegate transcript interpretation, take selection, B-roll choice, pacing, or visual treatment to ChatCut AI.**

Source footage is immutable. Write all generated artifacts beneath the project's `edit/` directory. Preserve speech whenever meaning, timing, or confidence is uncertain.

## Hard Gates

1. Run `video-editing-th doctor` before the first project on a machine.
2. Initialize with `video-editing-th project init <footage> --profile <profile>` and inventory it.
3. Transcribe each source using `video-editing-th transcribe ... --language th`.
4. Stop structural editing unless every source used in the plan passes the Thai quality gate. Read [references/thai-transcription.md](references/thai-transcription.md).
5. Use `video-editing-th analyze` to create compact transcript and retake evidence. Select the latest **complete** delivery, not blindly the last attempt.
6. Put exact source ranges, reasons, confidence, and review flags into a versioned `EditPlan`.
7. Validate with `video-editing-th plan validate` before rendering or touching ChatCut.

## Creative Pass

Index reusable media once. Query with `video-editing-th assets search`, inspect metadata/contact sheets, visually verify a shortlist, and then record the chosen source range in the plan. Read [references/asset-selection.md](references/asset-selection.md).

Add captions with `video-editing-th captions build`. Use motion, overlays, B-roll, and SFX only when they support a spoken idea; obey the active profile's frequency and gain limits.

## ChatCut Execution

Export ordered operations with `video-editing-th chatcut export`. Execute the manifest phase-by-phase through ChatCut MCP; use browser control only for an operation MCP cannot perform. Read [references/chatcut-execution.md](references/chatcut-execution.md).

Build a local structural preview with `video-editing-th render preview` before the creative NLE pass. Render from ChatCut, inspect the result, and use the bounded loop in [references/qa.md](references/qa.md). Do not present a preview that still has clipped speech, incorrect Thai captions, irrelevant assets, hidden text, or unsafe audio.
