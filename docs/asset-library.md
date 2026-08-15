# Asset Library

## Recommended organization

```text
VideoAssets/
├── broll/
│   ├── gym/
│   ├── food/
│   └── thailand/
├── overlays/
│   ├── arrows/
│   ├── checkmarks/
│   └── social-ui/
├── sfx/
│   ├── impacts/
│   ├── pops/
│   └── whooshes/
├── transitions/
├── backgrounds/
└── music/
```

Folder names help infer an asset role. The catalog also stores duration, resolution, orientation, audio presence, transparency hints, descriptions, tags, use cases, shot type, camera motion, and contact-sheet paths.

## Index once, update incrementally

```bash
video-editing-th assets index /local/VideoAssets \
  --catalog /local/VideoAssets/.video-editing-th/catalog.db \
  --preview-dir /local/VideoAssets/.video-editing-th/previews
```

Unchanged files are skipped by SHA-256. Changed files retain existing annotations. Missing files are removed from the catalog.

## Annotate

Codex can inspect an initial contact sheet and persist factual metadata:

```bash
video-editing-th assets annotate \
  --catalog /local/VideoAssets/.video-editing-th/catalog.db \
  asset-0123456789abcdef \
  --description "Close-up of an athlete performing incline dumbbell presses" \
  --tag gym --tag chest --tag hypertrophy \
  --use-case "Illustrate strength-training volume" \
  --shot-type close-up \
  --camera-motion handheld
```

Descriptions should state what is visibly present. Use cases may express editorial relevance. Do not claim brands, locations, people, or licensing status that cannot be verified.

## Retrieve and verify

```bash
video-editing-th assets search "incline dumbbell chest training" \
  --catalog /local/VideoAssets/.video-editing-th/catalog.db \
  --role broll \
  --orientation portrait \
  --limit 8
```

Search results are a shortlist, not an automatic placement decision. Codex checks contact sheets, inspects the strongest original clips when necessary, avoids repeated use, chooses exact source ranges, and records its reasoning in the plan.
