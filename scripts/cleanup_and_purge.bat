@echo off
echo This script rewrites git history to remove .env and other sensitive files.
where git-filter-repo >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo git-filter-repo not found. Install from https://github.com/newren/git-filter-repo
  exit /b 1
)

set /p yn=This will rewrite Git history. Have you communicated with your team? (yes/no) 
if /I NOT "%yn%"=="yes" (
  echo Aborting. Coordinate with your team before rewriting history.
  exit /b 1
)

git filter-repo --invert-paths --paths .env --force
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo History rewritten. Force-push manually:
echo   git push --force --all
echo   git push --force --tags
