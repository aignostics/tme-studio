> [!NOTE]
> This file is maintained by the foundry-python template and will be updated when you run `mise run update_from_template`.

# Troubleshooting

## CI Fails After Initial Push

**Cause**: Required services not configured.

**Solution**: Complete all sections in [docs/foundry/getting-started.md](getting-started.md).

## Missing Secret Errors

**Cause**: Repository secrets not configured.

**Solution**: Add required secrets at https://github.com/aignostics/tme-studio/settings/secrets/actions:
- `SONAR_TOKEN`

## Tests Not Running in CI

**Cause**: Tests missing category marker.

**Solution**: Add `@pytest.mark.unit`, `@pytest.mark.integration`, or `@pytest.mark.e2e` to each test.

## Pre-commit Hook Failures

**Cause**: Code doesn't meet quality standards.

**Solution**: Many hooks auto-fix issues. Re-stage files and commit:
```shell
git add <fixed-files>
git commit
```

## Coverage Dropping

**Cause**: New code not covered by tests.

**Solution**: Add tests for new code, or verify new tests have category markers.

## Commit Message Rejected

**Cause**: Message doesn't follow conventional commit format.

**Solution**: Use format `type(scope): description`. Valid types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf`, `ci`.

## Renovate PR Causes Test Failures

**Cause**: A dependency update introduced a breaking change.

**Solution**:
1. Check which package was updated in the Renovate PR description
2. Review the package changelog for breaking changes
3. Fix the compatibility issue in a commit on the Renovate branch (Renovate branches accept external commits)
4. If the fix is complex, close the Renovate PR and pin the dependency version in `pyproject.toml` until you can address it

---

## mise.lock Keeps Changing / Regenerating in CI

**Cause**: Version skew between the mise on your machine and the one pinned in CI.
`mise lock` output depends on the mise version (and host OS) that produced it, so when
your local mise differs from the `version:` pinned in the mise workflows
(`.github/workflows/mise-lock-sync.yml`, `.github/actions/setup-dev-env/`), the lockfile
you commit differs from what CI regenerates. A frequent culprit is the
`provenance_verified` attestation field, which newer mise versions write to the lockfile
and older ones omit.

**Solution** — align the two mise versions (either direction works):

1. **Update your local mise** to match the pinned CI version (see `version:` in the mise
   workflows): `mise self-update <version>`, **or**
2. **Bump the CI pin** to your local version — Renovate does this automatically via the
   `# renovate:` annotation on each pin, so merging the "bump mise CLI" Renovate PR is
   usually enough.

Note: the `mise-lock-sync` workflow regenerates `mise.lock` on Linux and commits it back
to your PR automatically, so skew usually shows up as a `chore: regenerate mise.lock`
commit on your branch rather than a hard failure. If that commit keeps reappearing,
aligning the versions above stops the churn.

---

## mise Fails with `RateLimitedError` (HTTP 403) in CI

**Cause**: `jdx/mise-action` v5.1.1+ keeps its GitHub token inside the action step. A
later step that calls the GitHub API through mise (`mise lock`, `mise use`, lazy tool
installs) goes out unauthenticated and shares GitHub's 60 requests/hour per runner IP.

**Solution**: give that step a token:

```yaml
- run: mise lock
  env:
    GITHUB_TOKEN: ${{ github.token }}
```

`persist_github_token: true` on mise-action also works, but exposes the token to every
later step in the job.

---

## Further Reading

- [README.md](../../README.md) - Project documentation
- [CODE_STYLE.md](../../CODE_STYLE.md) - Code style guide
- [SECURITY.md](../../SECURITY.md) - Security policy
- [CONTRIBUTING.md](../../CONTRIBUTING.md) - Contribution guidelines

---

## Feedback

Happy to hear from you if you have any feedback on the DX/UX of using `foundry-python`.
Please reach out on [Slack](https://aignostics.slack.com/archives/C0AEY02UQD6).
