from aiohttp import web

import asyncpg


async def create_pool(app: web.Application):
    app["pool"] = pool = await asyncpg.create_pool(dsn=app["dsn"])
    await pool.execute("CREATE TABLE IF NOT EXISTS cdn (data BYTEA, id TEXT)")


async def dispose_pool(app: web.Application):
    await app["pool"].close()


def add_tasks(app: web.Application):
    app.on_startup.append(create_pool)
    app.on_cleanup.append(dispose_pool)
