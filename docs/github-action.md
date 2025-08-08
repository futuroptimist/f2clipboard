# GitHub Action

The repository includes a composite action that runs the `f2clipboard` CLI.
Use it in your workflows to generate Codex summaries or copy files to the
clipboard.

```yaml
- uses: futuroptimist/f2clipboard@v1
  with:
    args: codex-task https://chatgpt.com/codex/tasks/task_123 --no-clipboard
```

The `args` input accepts any arguments supported by the CLI and defaults to
`--help`.
