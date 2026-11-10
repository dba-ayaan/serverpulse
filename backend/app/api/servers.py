from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.discovery import sync_prometheus_targets
from app.models.server import Server
from app.schemas.server import ServerCreate, ServerResponse

router = APIRouter(prefix="/api/v1/servers", tags=["Servers"])


def get_db():
    with SessionLocal() as db:
        yield db


@router.post("/", response_model=ServerResponse, status_code=201)
def create_server(
    payload: ServerCreate,
    db: Session = Depends(get_db),
):
    server = Server(**payload.model_dump())
    db.add(server)

    try:
        db.commit()
        db.refresh(server)
        sync_prometheus_targets(db)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409, "Server target already registered"
        )
    except OSError:
        raise HTTPException(
            500, "Server saved, but Prometheus discovery sync failed"
        )

    return server


@router.get("/", response_model=list[ServerResponse])
def list_servers(db: Session = Depends(get_db)):
    return db.scalars(
        select(Server).order_by(Server.id)
    ).all()


@router.get("/{server_id}", response_model=ServerResponse)
def get_server(
    server_id: int,
    db: Session = Depends(get_db),
):
    server = db.get(Server, server_id)

    if not server:
        raise HTTPException(404, "Server not found")

    return server


@router.delete("/{server_id}", status_code=204)
def delete_server(
    server_id: int,
    db: Session = Depends(get_db),
):
    server = db.get(Server, server_id)

    if not server:
        raise HTTPException(404, "Server not found")

    db.delete(server)
    db.commit()
    sync_prometheus_targets(db)
