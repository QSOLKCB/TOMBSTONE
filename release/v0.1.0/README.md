# TOMBSTONE v0.1.0 — source-only release candidate

This folder records the **post-merge** release-readiness evidence for source commit
`d6ae7d4016eb4efff6a684737711d809ec9d256f`.

Files:

- `SOURCE_COMMIT.txt`: exact proposed release source SHA and provenance.
- `POST_MERGE_EVIDENCE.md`: six successful push workflows **on the source merge SHA**, plus compiler, architecture, sanitizers, receipt continuity and trust limitations.

To generate candidate assets from a full Git checkout at or after this commit:

```sh
bash tools/package_candidate.sh
(cd dist/v0.1.0 && sha256sum -c --strict SHA256SUMS.txt)
```

The generated `dist/v0.1.0/` folder contains:

- `TOMBSTONE-v0.1.0-source.tar.gz` — deterministic `git archive` of the exact
  **Phase 7 merge commit**, not an archive of the packaging PR's altered HEAD.
- `SOURCE_COMMIT.txt` — provenance copy.
- `POST_MERGE_EVIDENCE.md` — post-merge CI record.
- `SHA256SUMS.txt` — **actual SHA-256 digests calculated over those three assets**.

The packaging script creates the archive twice and compares both copies, validates
essential tracked files, and verifies every recorded SHA256SUMS entry. It **refuses**
to overwrite an existing output directory.

The corresponding GitHub Actions workflow uploads these same four files as
a downloadable, temporary Actions artifact. An artifact is **not** a published
GitHub Release and its retention is limited to 30 days.

The initial candidate is *source-only*. It deliberately makes no claim about
portable prebuilt binaries. If binaries are later included in the release,
their exact bytes and digests must be added to the release manifest and tested
on their intended platform before publication.

**No release tag has been created.** A maintainer must inspect the actual
checksums, CI outcomes, release notes, limitations and exact tag target before
explicitly authorizing an immutable release.
