# Changelog

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and intends to use [Semantic Versioning](https://semver.org/spec/v2.0.0.html) for releases.

## [Unreleased]

### Added

- Automated lint, test, dependency audit, CodeQL, dependency review, and OpenSSF Scorecard workflows.
- Tests for command failures, pytest reporting, evidence ordering, gate validation, prompt caching, and skill metadata.
- Standard contribution, support, security, conduct, citation, and release documentation.

### Changed

- Verification records are written atomically with collision-resistant run IDs and per-gate timeouts.
- The Stop hook requires the newest recent evidence record to pass and returns a structured block decision.
- Structured command execution reports missing executables, permission failures, and timeouts with conventional exit codes.
- Prompt-cache guidance defers model thresholds to the current provider documentation.
