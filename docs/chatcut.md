# ChatCut Execution

## Operating model

Codex owns the edit. ChatCut supplies tracks, timeline controls, optional captions, native sound effects, native music, native transitions, audio mixing, motion/effects, and rendering. The workflow never asks ChatCut AI to interpret Thai, select takes, choose assets, or devise a creative direction.

## Export the manifest

```bash
video-editing-th chatcut export edit/plans/edit-plan.json \
  --output edit/plans/chatcut.json
```

The default composition is 1080x1920 at 30 fps. This is a built-in social-video default rather than a machine setting. Explicit format flags remain available for a project that requests another composition.

The manifest is ordered by phase:

1. imports of source footage and selected local visual assets;
2. structural source clips;
3. corrected captions, only when requested for this project;
4. local B-roll, overlays, and backgrounds;
5. zoom, pan, punch-in, and reframe operations;
6. ChatCut-native sound effects and music;
7. ChatCut-native transitions.

## Native references

A native ChatCut choice is represented by a stable `asset_id`, not a local path:

```json
{
  "kind": "sfx",
  "asset_id": "chatcut:sfx:soft-pop",
  "timeline_start": 4.2,
  "parameters": {"gain_db": -12}
}
```

```json
{
  "kind": "music",
  "asset_id": "chatcut:music:upbeat-clean",
  "timeline_start": 0,
  "timeline_end": 42.5,
  "parameters": {"gain_db": -24}
}
```

Native references are not included in import operations. Codex searches or previews the available ChatCut choices, makes the decision, records the reason/timing/level, and then executes it through MCP or browser controls.

## Captions

Captions are a current-prompt decision. When the user explicitly requests Thai captions, Codex builds corrected cues from the validated transcript and includes the caption phase. When the prompt is silent about captions, the plan and ChatCut manifest omit captions.

## Codex execution policy

- Use ChatCut MCP for structured operations, native-media search when exposed, and reads.
- After each material batch, inspect the project/timeline state.
- Use the browser only for an exact operation absent from MCP.
- Verify a browser-applied property visually or through a subsequent read.
- Import only source media and selected local visual assets, not the entire asset library.
- Keep structural cuts independent of the creative pass.
- Keep dialogue louder and clearer than native music or effects.
- Keep the ChatCut project open for manual adjustment after automated work.

The detailed agent contract lives in `skills/video-editing-th/references/chatcut-execution.md`.

## Rebuilding

The ChatCut project is not the sole record of the edit. Retain the canonical plan and manifest under `edit/plans/`; these contain source paths, ranges, output timings, reasons, confidence, native references, and creative operations.
