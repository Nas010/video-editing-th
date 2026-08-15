# Security Policy

## Supported version

Security fixes are applied to the current `main` branch and the latest tagged release.

## Reporting

Use GitHub's private vulnerability-reporting form from the repository's **Security** tab. Include affected version/commit, impact, reproduction steps, and a minimal proof of concept. Do not attach private footage, transcripts, API keys, account tokens, or personal asset libraries.

When private reporting is unavailable, open a public issue requesting a private contact channel without including exploit details.

## Sensitive data boundaries

The repository must never contain:

- `.env` files or API credentials;
- ChatCut/session tokens;
- raw or rendered private footage;
- transcripts containing private speech;
- asset indexes that reveal private absolute paths;
- model weights with incompatible redistribution terms.

The application transmits files to ChatCut only when Codex performs an explicitly authorized project import. Local transcription and analysis remain local unless a separately configured cloud backend is introduced by the operator.
