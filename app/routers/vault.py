from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Vault
from app.dependencies import get_current_user
from app.schemas import VaultBase

router = APIRouter(tags=["Vault"])


@router.post("/vaults")
def create_vault(
    vault: VaultBase,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_vault = (
        db.query(Vault)
        .filter(Vault.user_id == user.id, Vault.title == vault.title)
        .first()
    )
    if db_vault:
        raise HTTPException(status_code=409, detail="Vault already exists")

    db_vault = Vault(title=vault.title, user_id=user.id)
    db.add(db_vault)
    db.commit()
    return {"detail": "Vault created successfully"}
