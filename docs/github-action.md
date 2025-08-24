# GitHub Action

The repository includes a composite action that runs the `f2clipboard` CLI.
Use it in your workflows to generate Codex summaries or copy files to the
clipboard.

```yaml
- uses: futuroptimist/f2clipboard@v1
  with:
    args: codex-task https://chatgpt.com/codex/tasks/task_123 --no-clipboard
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

The `env` block passes tokens such as `GITHUB_TOKEN` for GitHub API access and optional keys for
log summarisation. The `args` input accepts any arguments supported by the CLI and defaults to
`--help`.
