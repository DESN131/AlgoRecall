from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.api.errors import api_error
from app.core.database import get_db
from app.models import Tag
from app.schemas.tag import TagCreate, TagRead

router = APIRouter(prefix="/tags", tags=["Tags"])
Db = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[TagRead])
def get_tags(db: Db, search: str | None = None):
    stmt = select(Tag)
    if search:
        stmt = stmt.where(Tag.name.ilike(f"%{search.strip()}%"))
    return list(db.scalars(stmt.order_by(Tag.name)))


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(payload: TagCreate, db: Db):
    name = payload.name.strip()
    if not name:
        raise api_error(422, "INVALID_TAG", "Tag name cannot be blank.")
    tag = Tag(name=name)
    db.add(tag)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise api_error(409, "TAG_ALREADY_EXISTS", f"Tag '{name}' already exists.")
    db.refresh(tag)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: int, db: Db):
    tag = db.get(Tag, tag_id)
    if not tag:
        raise api_error(404, "TAG_NOT_FOUND", f"Tag #{tag_id} not found.")
    db.delete(tag)
    db.commit()
    return Response(status_code=204)
