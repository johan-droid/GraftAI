from fastapi import APIRouter, Depends
from backend.auth.schemes import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
async def read_current_user(current_user=Depends(get_current_user)):
    return current_user


# Additional user endpoints can be added here
