from fastapi import APIRouter

router = APIRouter(tags=["Report"])


@router.post("/reports")
def create_report():
    pass
