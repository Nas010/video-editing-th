# Pressure scenario: first-use configuration

The user invokes `$video-editing-th /Users/example/Footage/Reel-01` on a freshly cloned machine and says only “edit this.” No local config exists.

Correct behavior: treat this as first-use configuration, run the configuration gate, and ask only for machine-specific facts such as the B-roll folder, overlay folder, sound-effects folder, and other optional asset locations. Never invent absolute paths. Save the one-time config outside Git, read it back with `video-editing-th config show`, then apply the complete default Thai fast-Reel mission without asking the user to repeat the editing brief.
