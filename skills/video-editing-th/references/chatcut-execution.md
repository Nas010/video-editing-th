# ChatCut Execution Contract

ChatCut implements the canonical edit plan. Codex remains the editor. Never ask ChatCut AI to choose takes, rewrite speech, select B-roll, choose native media, or invent the creative direction.

## Control order

1. Use ChatCut MCP for structured reads and writes.
2. Inspect the returned project/timeline state after each material batch.
3. Use browser control only as a fallback for a specific operation not exposed by MCP.
4. After browser interaction, verify the resulting visible timeline/property state before continuing.

Do not send sensitive files to a third party unless the user authorized that project upload. Import only project sources and shortlisted local visual assets, never the entire asset library.

## Composition

The default social composition is 1080x1920 at 30 fps. It is not a one-time configuration choice. Use another format only when the current project prompt explicitly requests it.

## Native media

Sound effects, music, and transitions are native to ChatCut in the normal workflow:

- **native sound**: Codex selects a ChatCut-native sound effect, timing, and level;
- **native music**: Codex selects a ChatCut-native music choice and keeps it below dialogue;
- **native transition**: Codex selects a ChatCut-native transition only when the editorial structure warrants it.

Represent native choices with stable `asset_id` references such as `chatcut:sfx:soft-pop` or `chatcut:music:upbeat-clean`. Do not add them to import operations because they are not local files. ChatCut supplies the media; Codex supplies the intent and decision.

## Captions

Only execute the caption phase when the current user prompt explicitly requested captions. When requested, use cues generated from the validated canonical transcript. If the prompt is silent about captions, the plan and ChatCut manifest should contain no caption operations.

## Manifest phases

Execute `chatcut.json` in its declared order:

1. **import** — sources and shortlisted local visual assets only;
2. **structure** — exact source clips, trims, output order, no creative effects;
3. **captions** — only requested corrected Thai cues;
4. **visuals** — local B-roll, overlays, and backgrounds;
5. **motion** — punch-ins, pans, zooms, reframes;
6. **audio** — planned ChatCut-native sound effects and music with explicit levels;
7. **transitions** — planned ChatCut-native transitions only.

The structural phase must be reviewable before later phases. Never let a creative operation change which spoken words are kept.

## Browser fallback

Before clicking, read the current editor state. Prefer accessible labels and DOM-backed controls. Do not guess coordinates when an inspectable control exists. Keep the editor tab open as the deliverable. If an operation cannot be verified, leave it unapplied and flag it instead of assuming success.

Custom motion graphics may be generated externally as transparent media and imported, but their placement still comes from the canonical plan.
