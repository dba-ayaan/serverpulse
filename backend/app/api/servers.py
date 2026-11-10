import httpx

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.discovery import sync_prometheus_targets
from app.models.server import Server
from app.schemas.server import (
    ServerCreate,
    ServerUpdate,
    ServerStatusUpdate,
    ServerResponse,
    ServerCheckResponse,
)

router = APIRouter(prefix="/api/v1/servers", tags=["Servers"])


def get_db():
    with SessionLocal() as db:
        yield db


def sync_discovery():
    try:
        with SessionLocal() as db:
            sync_prometheus_targets(db)
    except OSError:
        raise HTTPException(
            500,
            "Database updated, but Prometheus discovery sync failed"
        )


@router.post("/", response_model=ServerResponse, status_code=201)
def create_server(payload: ServerCreate, db: Session = Depends(get_db)):
    server = Server(**payload.model_dump())
    db.add(server)

    try:
        db.commit()
        db.refresh(server)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Server target already registered")

    sync_discovery()
    return server


@router.get("/", response_model=list[ServerResponse])
def list_servers(db: Session = Depends(get_db)):
    return db.scalars(select(Server).order_by(Server.id)).all()


@router.get("/{server_id}", response_model=ServerResponse)
def get_server(server_id: int, db: Session = Depends(get_db)):
    server = db.get(Server, server_id)

    if not server:
        raise HTTPException(404, "Server not found")

    return server


@router.put("/{server_id}", response_model=ServerResponse)
def update_server(
    server_id: int,
    payload: ServerUpdate,
    db: Session = Depends(get_db),
):
    server = db.get(Server, server_id)

    if not server:
        raise HTTPException(404, "Server not found")

    changes = payload.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(400, "No fields supplied for update")

    if any(value is None for value in changes.values()):
        raise HTTPException(422, "Fields cannot be null")

    for field, value in changes.items():
        setattr(server, field, value)

    try:
        db.commit()
        db.refresh(server)
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Server target already registered")

    sync_discovery()
    return server


@router.patch("/{server_id}/status", response_model=ServerResponse)
def update_server_status(
    server_id: int,
    payload: ServerStatusUpdate,
    db: Session = Depends(get_db),
):
    server = db.get(Server, server_id)

    if not server:
        raise HTTPException(404, "Server not found")

    server.enabled = payload.enabled
    db.commit()
    db.refresh(server)

    sync_discovery()
    return server


@router.get(
    "/{server_id}/check",
    response_model=ServerCheckResponse,
)
def check_server(server_id: int, db: Session = Depends(get_db)):
    server = db.get(Server, server_id)

    if not server:
        raise HTTPException(404, "Server not found")

    url = f"http://{server.hostname}:{server.exporter_port}/metrics"

    try:
        response = httpx.get(url, timeout=3.0, follow_redirects=False)

        is_node_exporter = (
            response.status_code == 200
            and "node_" in response.text
        )

        return ServerCheckResponse(
            reachable=is_node_exporter,
            status_code=response.status_code,
            message=(
                "Node Exporter is reachable"
                if is_node_exporter
                else "Endpoint responded, but Node Exporter metrics were not detected"
            ),
        )

    except httpx.TimeoutException:
        return ServerCheckResponse(
            reachable=False,
            message="Connection timed out",
        )

    except httpx.RequestError:
        return ServerCheckResponse(
            reachable=False,
            message="Unable to connect to Node Exporter",
        )


@router.delete("/{server_id}", status_code=204)
def delete_server(server_id: int, db: Session = Depends(get_db)):
    server = db.get(Server, server_id)

    if not server:
        raise HTTPException(404, "Server not found")

    db.delete(server)
    db.commit()

    sync_discovery()
