# Project Layout

A footage project remains separate from the code repository:

```text
my-reel/
├── clip-001.mov
├── clip-002.mov
└── edit/
    ├── project.json
    ├── analysis/
    │   └── clip-001/
    │       ├── takes_packed.md
    │       └── retake-groups.json
    ├── transcripts/
    │   ├── clip-001.json
    │   └── clip-001.quality.json
    ├── plans/
    │   ├── edit-plan.json
    │   ├── edit-plan-captioned.json
    │   └── chatcut.json
    ├── renders/
    │   └── rough-preview.mp4
    ├── qa/
    └── tmp/
```

`project init` creates only the generated `edit/` structure. Source media remains unchanged. `project inventory` ignores the top-level `edit/` directory, hashes supported media, and stores normalized metadata in `project.json`.

The canonical plan is the durable record of the edit. A ChatCut project can be rebuilt from the same plan and source paths, subject to the same software/model versions recorded by the run.

Large media, rendered output, local databases, model weights, and secrets belong outside this Git repository.
