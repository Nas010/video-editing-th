---
name: video-editing-th
description: Use when turning raw Thai talking-head footage into a polished vertical Reel with retake removal, optional prompt-requested captions, local visual asset selection, ChatCut-native audio/effects, Codex-controlled timeline execution, rendering, and QA.
---

# Thai Video Editing

## Principle

Codex makes every editorial and creative decision. ChatCut is an editable NLE execution surface, not the decision-maker. **Never delegate transcript interpretation, take selection, B-roll choice, pacing, captions, sound design, music choice, transitions, or visual treatment to ChatCut AI.**

Source footage is immutable. Write generated artifacts beneath the project's `edit/` directory. Preserve speech whenever meaning, timing, or confidence is uncertain.

## Invocation

The normal recurring request is:

```text
$video-editing-th <footage-folder>
```

The user does not need to repeat the entire editing brief. Treat extra instructions as a **per-project override** of the defaults below, not as a replacement for unspecified stages.

## Default Mission

**Unless the user overrides it**, turn the supplied raw Thai talking-head footage into a polished, fast-paced vertical social-media Reel:

- output at **1080x1920** and **30 fps**;
- remove mistakes, false starts, superseded retakes, and excess dead air;
- prefer the **latest complete** good take rather than blindly choosing the final attempt;
- tighten pacing without cutting through spoken words or Thai syllables;
- retrieve contextually relevant local **B-roll**, **overlays**, and backgrounds from the configured visual folders;
- choose and place **ChatCut-native sound effects**, **ChatCut-native music**, and **ChatCut-native transitions** when they improve the edit;
- add restrained semantic **punch-ins**, zooms, pans, and reframing where they improve comprehension or emphasis;
- build an editable ChatCut timeline through MCP first and browser control only when MCP lacks a required operation;
- render the result, inspect picture/audio/captions/effects, and repair defects through the bounded QA loop;
- retain the canonical transcript, quality report, analysis, edit plan, optional caption artifacts, ChatCut manifest, previews, and final render.

Only add captions when the current prompt explicitly requests them. If the prompt is silent about captions, omit them. When captions are requested, generate them from the validated canonical Thai transcript rather than ChatCut transcription.

The social-vertical composition is a built-in default, not a machine-configuration question. Use a different format only when the current project prompt explicitly requests one.

## Configuration Gate

Before the first project on a machine:

1. Run `video-editing-th config path` and check whether that file exists.
2. If it does not exist, run `video-editing-th configure` and ask the user only for machine-specific facts that cannot be inferred: the local B-roll folder, overlay/graphics folder, background folder, and default editing profile. Never invent paths.
3. Read the result with `video-editing-th config show --json`.
4. If any local visual folders are configured, run `video-editing-th assets index-configured` before the first creative pass and whenever those files change.
5. Do not ask for native ChatCut media libraries, composition size, frame rate, or captions during one-time setup.
6. Do not ask for the same paths on every project. Re-run the wizard only when the user asks to change settings or a configured path is invalid.

Read [references/configuration.md](references/configuration.md) for the one-time setup contract.

## Hard Gates

1. Run `video-editing-th doctor` before the first project on a machine. Run `video-editing-th models recommend` and verify the local ASR model/cache using [references/asr-models.md](references/asr-models.md).
2. Resolve the configured profile (normally `profiles/thai-fast-reel.yaml`), initialize with `video-editing-th project init <footage> --profile <profile>`, and inventory it.
3. Transcribe every source used in the edit with `video-editing-th transcribe ... --language th`.
4. Stop structural editing unless every used source passes the Thai quality gate. Read [references/thai-transcription.md](references/thai-transcription.md).
5. Use `video-editing-th analyze` to create compact transcript and retake evidence. Select the latest complete delivery, not blindly the last attempt.
6. Put exact source ranges, reasons, confidence, and review flags into a versioned `EditPlan`.
7. Validate with `video-editing-th plan validate` before rendering or touching ChatCut.

## Creative Pass

Use `video-editing-th assets search` only for configured local visual assets. Inspect metadata and contact sheets, visually verify a shortlist, and record the chosen source range and reason in the plan. Never use the highest text-search score without visual verification. Read [references/asset-selection.md](references/asset-selection.md).

For native sound effects, music, and transitions, Codex should inspect/search the options available through ChatCut and record a stable native asset reference plus reason, timing, and parameters in the plan. ChatCut provides the library; Codex still chooses what is used.

Run `video-editing-th captions build` only when the user explicitly asked for captions in the current prompt. Use motion, overlays, B-roll, native audio, and transitions only when they support a spoken idea; obey the active profile's frequency and gain limits.

## ChatCut Execution

Build a local structural preview with `video-editing-th render preview` before the creative NLE pass. Export ordered operations with `video-editing-th chatcut export`; the default composition is 1080x1920 at 30 fps unless the project explicitly overrides it. Execute the manifest phase-by-phase through ChatCut MCP; use browser control only for an operation MCP cannot perform. Read [references/chatcut-execution.md](references/chatcut-execution.md).

Render from ChatCut, inspect the result, and use the bounded loop in [references/qa.md](references/qa.md). Do not present a preview that still has clipped speech, incorrect requested captions, irrelevant assets, hidden text, unsafe audio, or obviously mistimed effects.
