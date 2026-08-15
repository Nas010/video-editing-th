# Render QA Contract

Run a deterministic local preview after structural planning, then a ChatCut preview after creative execution.

## Structural QA

- Listen across every cut boundary, including at least 1.5 seconds before and after.
- Reject clipped consonants, missing Thai syllables, duplicate words, unnatural audio pops, and accidental silence.
- Confirm every retake group resolves to the intended complete delivery.
- Compare preview duration and clip order with the plan.

## Caption QA

- Confirm Thai Unicode, wording, timing, line length, and safe placement.
- Check that captions follow the output timeline rather than original source time.
- Ensure overlays and B-roll never hide captions.

## Creative QA

- Verify each B-roll choice supports the current spoken idea.
- Check that source ranges avoid setup/tail frames and unwanted text.
- Check zoom/pan framing throughout the effect, not only at its first frame.
- Check overlay transparency, bounds, duration, and stacking.
- Listen to SFX with dialogue and confirm the profile gain ceiling is respected.

## Bounded repair loop

Perform at most three QA passes:

1. inspect and record concrete failures;
2. change only the affected plan/timeline operations;
3. render and re-check the same evidence.

After three passes, report remaining defects instead of looping or hiding uncertainty. A pass is successful only when fresh preview evidence supports it.
