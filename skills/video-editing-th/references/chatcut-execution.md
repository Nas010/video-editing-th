# ChatCut Execution Contract

ChatCut implements the canonical edit plan. Codex remains the editor. Never ask ChatCut AI to choose takes, rewrite speech, select assets, or invent the creative direction.

## Control order

1. Use ChatCut MCP for structured reads and writes.
2. Inspect the returned project/timeline state after each material batch.
3. Use browser control only as a fallback for a specific operation not exposed by MCP.
4. After browser interaction, verify the resulting visible timeline/property state before continuing.

Do not send sensitive files to a third party unless the user authorized that project upload. Import only project sources and shortlisted assets, never the entire asset library.

## Manifest phases

Execute `chatcut.json` in its declared order:

1. **import** — sources and selected assets;
2. **structure** — exact source clips, trims, output order, no creative effects;
3. **captions** — corrected Thai cues from the canonical plan;
4. **visuals** — B-roll and overlays;
5. **motion** — punch-ins, pans, zooms, reframes;
6. **audio** — SFX and explicit levels;
7. **transitions** — only planned transitions.

The structural phase must be reviewable before later phases. Never let a creative operation change which spoken words are kept.

## Browser fallback

Before clicking, read the current editor state. Prefer accessible labels and DOM-backed controls. Do not guess coordinates when an inspectable control exists. Keep the editor tab open as the deliverable. If an operation cannot be verified, leave it unapplied and flag it instead of assuming success.

Custom motion graphics may be generated externally as transparent media and imported, but their placement still comes from the canonical plan.
