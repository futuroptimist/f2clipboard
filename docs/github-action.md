# GitHub Action

The repository includes a composite action ([action.yml](../action.yml)) that runs the
`f2clipboard` CLI. See the README's [GitHub Action section](../README.md#github-action) for an
overview. Use the action in your workflows to generate Codex summaries or copy files to the
clipboard.

```yaml
- uses: futuroptimist/f2clipboard@v1
  with:
    args: codex-task https://chatgpt.com/codex/tasks/task_123 --no-clipboard
```

The `args` input accepts any arguments supported by the CLI and defaults to
`--help`.

Set tokens as environment variables to authenticate API requests:

```yaml
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}  # optional for log summarisation
```

See the [README](../README.md#getting-started) for environment setup.
