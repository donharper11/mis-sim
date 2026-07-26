from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/auth", tags=["auth"])


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def auth_stub(path: str):
    raise HTTPException(status_code=501, detail="Not implemented — module P4")

