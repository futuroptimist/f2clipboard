# Merge Conflict Resolution Roadmap

This checklist captures the workflow for resolving merge conflicts in pull requests.

- [ ] Fetch PR metadata and check out the PR branch
  - [ ] `git fetch origin pull/<PR_NUMBER>/head:pr-merge`
  - [ ] `git checkout pr-merge`
  - [ ] Determine the base branch (`main` or from PR metadata)
- [ ] Attempt automatic resolutions
  - [ ] Strategy A – merge with `-X ours` and run checks
    - [ ] `pre-commit run --files <modified_files>`
    - [ ] `pytest -q`
  - [ ] Strategy B – merge with `-X theirs` and run checks
    - [ ] `pre-commit run --files <modified_files>`
    - [ ] `pytest -q`
- [ ] If both strategies fail
  - [ ] Collect conflicting hunks: `git --no-pager diff --name-only --diff-filter=U`
  - [ ] Use the Codex merge-conflicts prompt to generate a patch
  - [ ] Apply the patch and rerun checks
- [ ] Post a PR comment summarizing the outcome (strategy used or need for manual review)
