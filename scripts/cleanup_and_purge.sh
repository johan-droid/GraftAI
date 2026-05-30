#!/usr/bin/env bash
set -euo pipefail
echo "This script rewrites git history to remove .env and other sensitive files."
if ! command -v git-filter-repo >/dev/null 2>&1; then
  echo "git-filter-repo not found. Install with: pip install git-filter-repo"
  exit 1
fi

read -p "This will rewrite Git history. Have you communicated with your team? (yes/no) " yn
if [[ "$yn" != "yes" ]]; then
  echo "Aborting. Coordinate with your team before rewriting history."
  exit 1
fi

git filter-repo --invert-paths --paths .env --force
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo "History rewritten. You must force-push branches and tags after review:"
echo "  git push --force --all"
echo "  git push --force --tags"
