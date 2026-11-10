import json
import os
import tempfile

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.server import Server

TARGET_FILE = "/etc/prometheus/targets/servers.json"


def sync_prometheus_targets(db: Session) -> None:
    servers = db.scalars(
        select(Server).where(Server.enabled.is_(True))
    ).all()

    targets = []

    for server in servers:
        targets.append({
            "targets": [
                f"{server.hostname}:{server.exporter_port}"
            ],
            "labels": {
                "server_id": str(server.id),
                "server_name": server.name,
                "environment": server.environment,
            },
        })

    directory = os.path.dirname(TARGET_FILE)
    os.makedirs(directory, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(
        dir=directory,
        prefix="servers-",
        suffix=".json",
    )

    try:
        with os.fdopen(fd, "w") as file:
            json.dump(targets, file, indent=2)

        os.replace(temp_path, TARGET_FILE)

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
