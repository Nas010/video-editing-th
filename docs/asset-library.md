# Asset Library

## Configure local visual folders once

Run:

```bash
video-editing-th configure
```

The wizard accepts separate optional folders for B-roll, overlays/graphics, and backgrounds. They may live under one shared root or in different locations and drives.

A conventional shared layout is:

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
└── backgrounds/
```

With role-specific configuration, the saved role is authoritative; the directory name does not need to contain `broll`, `overlays`, or `backgrounds`.

Sound effects, music, and transitions come from ChatCut's native libraries in the normal workflow and are not indexed as machine-local dependencies.

## Index configured folders together

```bash
video-editing-th assets index-configured
```

Every configured visual root is scanned as one logical library. Pruning happens only after the combined scan, so refreshing B-roll cannot remove overlays or backgrounds stored in another configured folder.

The default catalog and contact-sheet locations come from the one-time config. Unchanged files are skipped by SHA-256. Changed files retain existing annotations. Files missing from all configured visual roots are removed from the catalog.

The catalog stores duration, resolution, orientation, audio presence, transparency hints, descriptions, tags, use cases, shot type, camera motion, and contact-sheet paths.

## Index an explicit conventional root

The original explicit command remains available for ad hoc libraries:

```bash
video-editing-th assets index /local/VideoAssets \
  --catalog /local/VideoAssets/.video-editing-th/catalog.db \
  --preview-dir /local/VideoAssets/.video-editing-th/previews
```

For this explicit form, folder names help infer each asset role, and the generic indexer still understands audio/transition roles for advanced uses. Because a single-root scan prunes against that root, use `index-configured` for the normal persistent visual catalog.

## Annotate

Codex can inspect an initial contact sheet and persist factual metadata. The configured catalog is used automatically:

```bash
video-editing-th assets annotate \
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
  --role broll \
  --orientation portrait \
  --limit 8
```

Search results are a shortlist, not an automatic placement decision. Codex checks contact sheets, inspects the strongest original clips when necessary, avoids repeated use, chooses exact source ranges, and records its reasoning in the plan.

For native sound effects, music, and transitions, Codex searches/previews the choices inside ChatCut and records stable native references in the edit plan instead of local file paths.

## Missing categories

Visual asset folders are optional. When no overlay or background folder is configured, the skill omits that local category and still produces a talking-head edit. If no visual folders at all are configured, `assets index-configured` reports a clear configuration error but structural editing and ChatCut-native creative choices remain available.
