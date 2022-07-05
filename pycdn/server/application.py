import asyncio
from typing import Optional
from loguru import logger
from aiohttp import web

from .routes import add_routes
from .startup import add_tasks


@web.middleware
async def middleware(request: web.Request, handler):
    resp = await handler(request)
    logger.debug(f"{request.method} {request.remote}: {request.path} {resp.status}")
    return resp


class Application:
    def __init__(self, dsn: str, auth: Optional[str] = None):
        self.app = web.Application(middlewares=[middleware])
        self.app["dsn"] = dsn
        self.make = self.make_app
        self.app["auth"] = auth

    def _make_app(self):
        add_routes(self.app)
        add_tasks(self.app)
        return self.app

    def run(self, host: str = "127.0.0.1", port: int = 5000):
        self._make_app()
        web.run_app(self.app, host=host, port=port)

    async def make_app(self):
        add_routes(self.app)
        add_tasks(self.app)
        return self.app

    async def __aenter__(self):
        return await self.make_app()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
