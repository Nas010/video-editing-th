# Asset Selection Contract

## Persistent local visual catalog

Do not inspect the entire local visual library for every edit. Run `video-editing-th assets index-configured` incrementally, then annotate B-roll, overlays, and backgrounds with factual descriptions, tags, use cases, shot type, and camera motion. The SQLite catalog retains file hashes and contact-sheet paths.

Sound effects, music, and transitions are not machine-local catalog requirements for the normal workflow. They come from ChatCut's native libraries and are selected during ChatCut planning/execution.

## Local visual retrieval

For each possible B-roll, overlay, or background slot:

1. State the spoken idea and the visual intent.
2. Query a role-filtered asset shortlist with `video-editing-th assets search`.
3. Reject candidates with the wrong aspect ratio, duration, subject, visual direction, licensing status, or repeated recent use.
4. Open contact sheets for the strongest candidates.
5. Perform visual verification on the final candidates; inspect the original clip only when the contact sheet cannot resolve timing or content.
6. Record asset ID/path, exact source range, timeline range, reason, confidence, and review state in the canonical plan.

Semantic similarity is retrieval evidence, not permission to place a file automatically.

## ChatCut-native retrieval

For a sound-effect, music, or transition opportunity:

1. State the editorial intent, desired character, timing, and acceptable intensity.
2. Search or inspect ChatCut's native choices through MCP when possible, otherwise through the browser.
3. Preview the strongest candidate when ChatCut supports previewing it.
4. Record the native asset reference in `asset_id`, for example `chatcut:sfx:soft-pop` or `chatcut:music:upbeat-clean`.
5. Record timing, gain or transition parameters, reason, confidence, and review state.
6. Verify the placed result after execution.

ChatCut supplies the library. Codex makes the selection. Never ask ChatCut AI to decide what fits the content.

## Placement rules

- B-roll replaces the talking-head picture while retaining dialogue unless the plan explicitly says otherwise.
- Overlays remain on higher tracks and must not cover faces, requested captions, or essential source text.
- Native sound effects must match the visual/editorial event and stay below the profile's gain limit.
- Native music must remain subordinate to dialogue and must not be added merely because a track exists.
- Native transitions should communicate a real topic or scene change; ordinary talking-head cuts normally remain hard cuts.
- Avoid repetitive punch-ins, repeated assets, and decorative effects with no editorial purpose.
- When no candidate clearly supports the idea, leave the talking head visible or use no effect rather than inserting irrelevant media.
