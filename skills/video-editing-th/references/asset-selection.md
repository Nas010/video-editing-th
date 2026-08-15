# Asset Selection Contract

## Persistent catalog

Do not inspect the entire library for every edit. Run `video-editing-th assets index` incrementally, then annotate assets with factual descriptions, tags, use cases, shot type, and camera motion. The SQLite catalog retains file hashes and contact sheet paths.

## Retrieval

For each possible B-roll, overlay, transition, or sound-effect slot:

1. State the spoken idea and the visual/audio intent.
2. Query a role-filtered asset shortlist with `video-editing-th assets search`.
3. Reject candidates with the wrong aspect ratio, duration, subject, visual direction, licensing status, or repeated recent use.
4. Open contact sheets for the strongest candidates.
5. Perform visual verification on the final candidates; inspect the original clip only when the contact sheet cannot resolve timing or content.
6. Record asset ID/path, exact source range, timeline range, reason, confidence, and review state in the canonical plan.

Semantic similarity is retrieval evidence, not permission to place a file automatically.

## Placement rules

- B-roll replaces the talking-head picture while retaining dialogue unless the plan explicitly says otherwise.
- Overlays remain on higher tracks and must not cover faces, captions, or essential source text.
- SFX must match the visual event and stay below the profile's gain limit.
- Avoid repetitive punch-ins, repeated assets, and decorative effects with no editorial purpose.
- When no candidate clearly supports the idea, leave the talking head visible rather than inserting irrelevant media.
