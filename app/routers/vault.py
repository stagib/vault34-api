from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Vault, Post
from app.dependencies import get_current_user
from app.schemas import VaultBase, VaultResponse, PostBase

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


@router.get("/vaults/{vault_id}/posts", response_model=VaultResponse)
def get_vault(vault_id: int, db: Session = Depends(get_db)):
    db_vault = db.query(Vault).filter(Vault.id == vault_id).first()
    if not db_vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    return db_vault


@router.post("/vaults/{vault_id}/posts")
def add_post(
    post: PostBase,
    vault_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_vault = (
        db.query(Vault).filter(Vault.id == vault_id, Vault.user_id == user.id).first()
    )
    if not db_vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    db_post = db.query(Post).filter(Post.id == post.id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    db_vault.posts.append(db_post)
    db.commit()
    db.refresh(db_vault)
    return db_vault.title


@router.delete("/vaults/{vault_id}/posts")
def delete_post(
    post: PostBase,
    vault_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_vault = (
        db.query(Vault).filter(Vault.id == vault_id, Vault.user_id == user.id).first()
    )
    if not db_vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    db_post = db.query(Post).filter(Post.id == post.id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not db_post in db_vault.posts:
        raise HTTPException(status_code=400, detail="Post not in vault")

    db_vault.posts.remove(db_post)
    db.commit()
    db.refresh(db_vault)
    return {"detail": "Removed post from vault"}
