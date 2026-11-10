import asyncio
import time

import httpx
from fastapi import APIRouter, HTTPException, Query

from app.core.config import settings

router = APIRouter(prefix="/api/v1/metrics", tags=["Metrics"])

BASE = 'job="node-exporter"'

QUERIES = {
    "cpu": (
        f'100 * (1 - avg by(server_id,server_name,environment) '
        f'(rate(node_cpu_seconds_total{{{BASE},mode="idle"}}[5m])))'
    ),
    "memory": (
        f'100 * (1 - node_memory_MemAvailable_bytes{{{BASE}}} / '
        f'node_memory_MemTotal_bytes{{{BASE}}})'
    ),
"disk": (
    f'100 * (1 - '
    f'max by(server_id,server_name,environment) '
    f'(node_filesystem_avail_bytes{{{BASE},fstype="ext4",mountpoint="/etc/hostname"}} / '
    f'node_filesystem_size_bytes{{{BASE},fstype="ext4",mountpoint="/etc/hostname"}}))'
),    
"up": f'up{{{BASE}}}',
}


def build_query(metric_name: str, server_id: int | None = None):
    if metric_name not in QUERIES:
        raise HTTPException(404, "Unknown metric")

    query = QUERIES[metric_name]

    if server_id is not None:
        query = query.replace(BASE, f'{BASE},server_id="{server_id}"')

    return query


async def prometheus_request(endpoint: str, params: dict):
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                f"{settings.prometheus_url}/api/v1/{endpoint}",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        if data.get("status") != "success":
            raise HTTPException(502, "Prometheus query failed")

        return data["data"]

    except httpx.HTTPError as exc:
        raise HTTPException(503, "Prometheus unavailable") from exc
    except ValueError as exc:
        raise HTTPException(502, "Invalid Prometheus response") from exc


@router.get("/summary")
async def metrics_summary(
    server_id: int | None = Query(default=None, ge=1),
):
    names = ["cpu", "memory", "disk", "up"]

    results = await asyncio.gather(*[
        prometheus_request(
            "query",
            {"query": build_query(name, server_id)},
        )
        for name in names
    ])

    return {
        name: result["result"]
        for name, result in zip(names, results)
    }


@router.get("/history/{metric_name}")
async def metrics_history(
    metric_name: str,
    server_id: int | None = Query(default=None, ge=1),
    hours: int = Query(default=1, ge=1, le=168),
    step: int = Query(default=60, ge=15, le=3600),
):
    query = build_query(metric_name, server_id)

    end = int(time.time())
    start = end - hours * 3600

    data = await prometheus_request(
        "query_range",
        {
            "query": query,
            "start": start,
            "end": end,
            "step": step,
        },
    )

    return {
        "metric": metric_name,
        "server_id": server_id,
        "hours": hours,
        "step": step,
        "results": data["result"],
    }


@router.get("/{metric_name}")
async def get_metric(
    metric_name: str,
    server_id: int | None = Query(default=None, ge=1),
):
    data = await prometheus_request(
        "query",
        {"query": build_query(metric_name, server_id)},
    )

    return {
        "metric": metric_name,
        "results": data["result"],
    }
