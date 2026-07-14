# Releasing

1. Confirm `main` is green and the dependency audit has no unresolved findings.
2. Move relevant entries from `Unreleased` in `CHANGELOG.md` into a dated version section.
3. Update `project.version` in `pyproject.toml` and `version` in `CITATION.cff`.
4. Open and merge a release pull request.
5. Create a signed tag in the form `vMAJOR.MINOR.PATCH` from the merge commit.
6. Create a GitHub release from the tag and copy the matching changelog section into the release notes.
7. Verify the release page, source archive, and workflow results.

The repository does not publish a package artifact. Releases identify tested source snapshots.
