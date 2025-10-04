# Merge Conflict Resolution Roadmap

This checklist captures the workflow for resolving merge conflicts in pull requests.

- [ ] Fetch PR metadata and check out the PR branch
  - [ ] `git fetch origin pull/<PR_NUMBER>/head:pr-merge`
  - [ ] `git checkout pr-merge`
  - [ ] Determine the base branch (`main` or from PR metadata)
- [x] Attempt automatic resolutions (use `f2clipboard merge-resolve`)
- [x] Strategy A – merge with `-X ours` and run checks (`f2clipboard merge-resolve --strategy ours`)
  - [x] `pre-commit run --files <modified_files>` (use `f2clipboard merge-checks`)
  - [x] `pytest -q` (covered by `f2clipboard merge-checks`)
- [x] Strategy B – merge with `-X theirs` and run checks (`f2clipboard merge-resolve --strategy theirs`)
  - [x] `pre-commit run --files <modified_files>` (use `f2clipboard merge-checks`)
  - [x] `pytest -q` (covered by `f2clipboard merge-checks`)
- [ ] If both strategies fail
  - [x] Collect conflicting hunks: `git --no-pager diff --name-only --diff-filter=U`
  - [x] Use the Codex merge-conflicts prompt to generate a patch (emitted by `merge-resolve`)
  - [ ] Apply the patch and rerun checks
- [ ] Post a PR comment summarizing the outcome (strategy used or need for manual review)
