# ChatCut Execution

## Operating model

Codex owns the edit. ChatCut supplies tracks, timeline controls, captions, audio mixing, motion/effects, and rendering. The workflow never asks ChatCut AI to interpret Thai, select takes, choose assets, or devise a creative direction.

## Export the manifest

```bash
video-editing-th chatcut export edit/plans/edit-plan-captioned.json \
  --output edit/plans/chatcut.json \
  --width 1080 \
  --height 1920 \
  --fps 30
```

The manifest is ordered by phase:

1. imports;
2. structural source clips;
3. corrected captions;
4. B-roll and overlays;
5. zoom, pan, punch-in, and reframe operations;
6. SFX;
7. transitions.

## Codex execution policy

- Use ChatCut MCP for structured operations and reads.
- After each material batch, inspect the project/timeline state.
- Use the browser only for an exact operation absent from MCP.
- Verify a browser-applied property visually or through a subsequent read.
- Import only source media and selected assets, not the entire asset library.
- Keep structural cuts independent of the creative pass.
- Keep the ChatCut project open for manual adjustment after automated work.

The detailed agent contract lives in `skills/video-editing-th/references/chatcut-execution.md`.

## Rebuilding

The ChatCut project is not the sole record of the edit. Retain the canonical plan and manifest under `edit/plans/`; these contain source paths, ranges, output timings, reasons, confidence, and creative operations.
