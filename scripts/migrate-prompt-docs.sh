#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

declare -A RENAMES=(
  ["docs/prompts-codex.md"]="docs/prompts/codex/overview.md"
  ["docs/prompts-codex-ci-fix.md"]="docs/prompts/codex/ci-fix.md"
  ["docs/prompts-codex-docs.md"]="docs/prompts/codex/docs.md"
  ["docs/prompts/prompts-codex.md"]="docs/prompts/codex/overview.md"
  ["docs/prompts/prompts-codex-ci-fix.md"]="docs/prompts/codex/ci-fix.md"
  ["docs/prompts/prompts-codex-docs.md"]="docs/prompts/codex/docs.md"
)

migrate() {
  local src="$1"
  local dest="$2"
  local abs_src="$repo_root/$src"
  local abs_dest="$repo_root/$dest"

  if [[ -f "$abs_src" ]]; then
    mkdir -p "$(dirname "$abs_dest")"
    mv "$abs_src" "$abs_dest"
    printf 'Moved %s -> %s\n' "$src" "$dest"
  fi
}

for src in "${!RENAMES[@]}"; do
  migrate "$src" "${RENAMES[$src]}"
done
