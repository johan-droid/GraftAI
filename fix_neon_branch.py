with open(".github/workflows/neon-branch-for-pr.yaml", "r") as f:
    content = f.read()

# I can see `Could not parse SQLAlchemy URL from given URL string` in Create Neon Branch!
# The variable `DATABASE_URL` is empty string!
# Why is it empty string?
# `DATABASE_URL: "${{ steps.create_neon_branch.outputs.db_url_with_pooler }}"`
# Maybe `steps.create_neon_branch.outputs.db_url_with_pooler` is empty, or the job is missing the correct variable?
# Looking closely at neon action:
# neondatabase/create-branch-action@v6
