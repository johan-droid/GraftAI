#!/bin/bash
git checkout -b fix-neon-branch-v6
sed -i 's/uses: neondatabase\/create-branch-action@v6/uses: neondatabase\/create-branch-action@v5/g' .github/workflows/neon-branch-for-pr.yaml
git add .github/workflows/neon-branch-for-pr.yaml
git commit -m "Downgrade neon create-branch-action to v5"
