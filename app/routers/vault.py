from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Vault, Post, PostFile
from app.schemas import VaultBase, VaultResponse, PostBase
from app.utils import get_current_user

router = APIRouter(tags=["Vault"])


@router.post("/vaults", response_model=VaultResponse)
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

    db_vault = Vault(title=vault.title, user_id=user.id, privacy=vault.privacy)
    db.add(db_vault)
    db.commit()
    return db_vault


@router.get("/vaults/{vault_id}", response_model=VaultResponse)
def get_vault(
    vault_id: int,
    db: Session = Depends(get_db),
):
    db_vault = db.query(Vault).filter(Vault.id == vault_id).first()
    if not db_vault:
        raise HTTPException(status_code=404, detail="Vault not found")
    return db_vault


@router.put("/vaults/{vault_id}", response_model=VaultResponse)
def update_vault(
    vault: VaultBase,
    vault_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_vault = (
        db.query(Vault).filter(Vault.id == vault_id, Vault.user_id == user.id).first()
    )
    if not db_vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    for key, value in vault.model_dump(exclude_unset=True).items():
        setattr(db_vault, key, value)

    db.commit()
    db.refresh(db_vault)
    return db_vault


@router.delete("/vaults/{vault_id}")
def delete_vault(
    vault_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_vault = (
        db.query(Vault).filter(Vault.id == vault_id, Vault.user_id == user.id).first()
    )
    if not db_vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    db.delete(db_vault)
    db.commit()
    return {"detail": "Successfully deleted vault"}


@router.get("/vaults/{vault_id}/posts", response_model=Page[PostBase])
def get_vault_posts(vault_id: int, db: Session = Depends(get_db)):
    db_vault = db.query(Vault).filter(Vault.id == vault_id).first()
    if not db_vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    paginated_posts = paginate(db_vault.posts)
    for post in paginated_posts.items:
        post_file = db.query(PostFile).filter(PostFile.post_id == post.id).first()
        if post_file:
            post.thumbnail = (
                f"{settings.API_URL}/posts/{post.id}/files/{post_file.filename}"
            )
    return paginated_posts


@router.post("/vaults/{vault_id}/posts/{post_id}")
def add_post_to_vault(
    post_id: int,
    vault_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_vault = (
        db.query(Vault).filter(Vault.id == vault_id, Vault.user_id == user.id).first()
    )
    if not db_vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    vault_post = any(post_id == post.id for post in db_vault.posts)
    if vault_post:
        raise HTTPException(status_code=404, detail="Post is already in vault")

    db_vault.posts.append(db_post)
    db.commit()
    db.refresh(db_vault)
    return {"detail": "Added post to vault"}


@router.delete("/vaults/{vault_id}/posts/{post_id}")
def delete_post_from_vault(
    post_id: int,
    vault_id: int,
    user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_vault = (
        db.query(Vault).filter(Vault.id == vault_id, Vault.user_id == user.id).first()
    )
    if not db_vault:
        raise HTTPException(status_code=404, detail="Vault not found")

    db_post = db.query(Post).filter(Post.id == post_id).first()
    if not db_post:
        raise HTTPException(status_code=404, detail="Post not found")

    if not db_post in db_vault.posts:
        raise HTTPException(status_code=400, detail="Post not in vault")

    db_vault.posts.remove(db_post)
    db.commit()
    db.refresh(db_vault)
    return {"detail": "Removed post from vault"}
