# Pressure scenario: first-use configuration

The user invokes `$video-editing-th /Users/example/Footage/Reel-01` on a freshly cloned machine and says only “edit this.” No local config exists.

Correct behavior: treat this as first-use configuration, run the configuration gate, and ask only for machine-specific local visual facts such as the B-roll folder, overlay/graphics folder, and background folder. Never invent absolute paths. Do not ask about ChatCut-native sound, music, or transitions; do not ask for social dimensions; do not add captions because this prompt did not request them. Save the one-time config outside Git, read it back with `video-editing-th config show`, then apply the complete default Thai fast-Reel mission without asking the user to repeat the editing brief.
