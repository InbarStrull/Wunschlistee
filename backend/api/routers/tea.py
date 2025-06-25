from fastapi import APIRouter


router = APIRouter()


@router.get("/teas")
async def root():
    return {"message": "teas"}


