# Third-Party Notices

## browser-use/video-use

This repository incorporates and adapts portions of `browser-use/video-use` at commit `92c2b34e44c205cbc2acae7f6ca7c1c219d5dd66`.

```text
MIT License

Copyright (c) 2026 Browser Use

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Runtime and optional dependencies

The package depends on or interoperates with separately distributed projects. Their own distributions and license files remain authoritative.

| Project | Role | License family |
|---|---|---|
| Pydantic | Canonical validation | MIT |
| PyYAML | Configuration | MIT |
| Rich | Terminal output | MIT |
| Typer | CLI | MIT |
| FFmpeg | Probe/render/silence/contact sheets | LGPL/GPL depending build |
| ggml-org/whisper.cpp | Optional local ASR | MIT |
| SYSTRAN/faster-whisper | Optional local ASR | MIT |
| Breakthrough/PySceneDetect | Optional scene detection | BSD-3-Clause |
| AcademySoftwareFoundation/OpenTimelineIO | Optional interchange | Apache-2.0 |
| WyattBlue/auto-editor | Optional timeline/media utility | Unlicense/public domain dedication |

ChatCut is an external service/integration and is not redistributed by this repository.
