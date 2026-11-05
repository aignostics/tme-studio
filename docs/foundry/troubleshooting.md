> [!NOTE]
> Maintained by [foundry-python](https://github.com/aignostics/foundry-python) and updated by `mise run update_from_template`. Changed it? [Send it upstream](README.md#changed-a-template-file-send-it-upstream).

# Troubleshooting

## CI Fails After the First Push

Complete [getting-started.md](getting-started.md). No per-repo secrets are needed: `SONAR_TOKEN`, GAR access (WIF) and the Claude and Slack tokens are org-level.

## "Tests without a category marker" Usage Error

Add `@pytest.mark.unit`, `@pytest.mark.integration` or `@pytest.mark.e2e` to each listed test. Without one, CI would never run it.

## Coverage Floor or Sonar Quality Gate Fails

`mise run test:coverage` reports the files below the floor. Add tests, or check that new tests have a category marker. The Sonar gate measures new code only; see the PR's SonarCloud check for the uncovered lines.

## Pre-commit Hook Failures

Many hooks fix files themselves. Stage the fixes and commit again.

## Commit Message Rejected

Commits and PR titles: `type(scope): description`, with a type Commitizen knows. See [Conventional Commits](ci-cd.md#conventional-commits).

## Renovate PR Breaks Tests

1. Check which package changed, and its changelog.
2. Push a fix to the Renovate branch (it accepts commits).
3. If the fix is large, close the PR and cap the version in `pyproject.toml` until you can address it.

## `update_from_template` Leaves `*.rej` Files or Conflicts Every Time

The template changed lines you edited locally. Merge each `*.rej` by hand and delete it. If the same file conflicts on every update, your edit belongs upstream: [send it to foundry-python](README.md#changed-a-template-file-send-it-upstream).

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

## Feedback

Feedback on foundry-python is welcome in [#topic-foundry](https://aignostics.slack.com/archives/C0AEY02UQD6). Fixes are even better: [send them upstream](README.md#changed-a-template-file-send-it-upstream).
