from __future__ import annotations

import asyncpg

from aiohttp import web


async def create_pool(app: web.Application) -> None:
    app["pool"] = pool = await asyncpg.create_pool(dsn=app["dsn"])
    await pool.execute(
        "CREATE TABLE IF NOT EXISTS cdn (data BYTEA, id TEXT, mime_type TEXT)"
    )


async def dispose_pool(app: web.Application) -> None:
    await app["pool"].close()


def add_tasks(app: web.Application) -> None:
    app.on_startup.append(create_pool)
    app.on_cleanup.append(dispose_pool)
