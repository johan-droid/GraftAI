with open(".github/workflows/neon-branch-for-pr.yaml", "r") as f:
    content = f.read()

# Ah! In outputs:
# db_url: ${{ steps.create_neon_branch_encode.outputs.db_url }}
# But there is no step called `create_neon_branch_encode`!
# The step is called `create_neon_branch`.
# So it should be `${{ steps.create_neon_branch.outputs.db_url_with_pooler }}`.
# BUT wait! `DATABASE_URL: "${{ steps.create_neon_branch.outputs.db_url_with_pooler }}"` was what was passed, and it was empty because `db_url_with_pooler` is not the standard output for v6?
# Wait! Let's check `neondatabase/create-branch-action` docs online if possible.
# Actually, if we look at the outputs, it says:
# `db_url: ${{ steps.create_neon_branch_encode.outputs.db_url }}`
# Let's fix the outputs to use `steps.create_neon_branch`
