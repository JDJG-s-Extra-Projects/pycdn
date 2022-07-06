from __future__ import annotations

import secrets
import string
import sys

from dataclasses import dataclass
from io import BytesIO
from typing import Any

from aiohttp import web
from loguru import logger
from magic import from_buffer


@dataclass
class Value:
    value: Any
    uses: int


class Cache:
    def __init__(self, max_uses: int = 10) -> None:
        self.cache: dict = {}
        self.max_uses: int = max_uses

    def get(self, key: str) -> Any:
        if key in self.cache:
            value = self.cache[key]
            value.uses += 1
            if value.uses > self.max_uses:
                del self.cache[key]
            return value.value
        return None

    def set(self, key: str, value: Any) -> None:
        if key in self.cache:
            self.cache[key].value = value
        else:
            self.cache[key] = Value(value, 1)


def generate_id() -> str:
    return "".join(secrets.choice(alphabet) for _ in range(8))


async def check_auth(app: web.Application, request: web.Request) -> tuple[bool, Any]:
    if not app["auth"]:
        return False, web.Response

    auth = request.headers.get("Authorization")
    if not auth or auth != app["auth"]:
        return False, web.Response

    return True, None


routes = web.RouteTableDef()
alphabet = string.ascii_lowercase + string.ascii_uppercase + string.digits
cache: Cache = Cache()

logger.add(
    sys.stdout, colorize=True, format="<green>{time}</green> <level>{message}</level>"
)


@routes.get("/files/{id}")
async def get_file(request: web.Request) -> web.Response:
    id = request.match_info["id"]
    is_cache = cache.get(id)

    if is_cache:
        logger.info(f"Found in cache: {id}")
        logger.info(f"Displaying image: {id}")
        return web.Response(
            body=is_cache, content_type=from_buffer(is_cache, mime=True)
        )

    app = request.app
    logger.info(f"Displaying image: {id}")
    data = (await app["pool"].fetchrow("SELECT * from cdn WHERE id = $1", id))["data"]
    buffer = BytesIO(data)

    return web.Response(body=buffer.getvalue(), content_type=data["mime_type"])


@routes.post("/upload")
async def post_file(request: web.Request) -> web.Response:
    app = request.app
    is_auth, resp = await check_auth(app, request)

    if not is_auth:
        logger.error("Unauthorized")
        if resp:
            return resp(status=401, text="Invalid authorization")

        return web.Response(status=401, text="Invalid authorization")
    post_data: Any = await request.post()
    file_data = post_data["file"].file.read()
    file_type = from_buffer(file_data, mime=True)

    id = generate_id()
    logger.info(f"Storing image: {id}")
    cache.set(id, file_data)
    logger.info(f"Uploading image: {id}")

    await app["pool"].execute(
        "INSERT INTO cdn(data, id, mime_type) VALUES ($1, $2, $3)",
        file_data,
        id,
        file_type,
    )
    return web.json_response(({"result": "success", "id": id}))


def add_routes(app: web.Application):
    app.add_routes(routes)
