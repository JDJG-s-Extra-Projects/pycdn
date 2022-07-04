import asyncio
from typing import Optional
from aiohttp import web

from .routes import add_routes
from .startup import add_tasks


class Application:
    def __init__(self, dsn: str, auth: Optional[str] = None):
        self.app = web.Application()
        self.app["dsn"] = dsn
        self.make = self.make_app
        self.app["auth"] = auth

    async def make_app(self):
        add_routes(self.app)
        add_tasks(self.app)
        return self.app

    def run(self, host: str = "localhost", port: int = 8080):
        asyncio.create_task(self())
        web.run_app(self.app, host=host, port=port)

    async def __call__(self):
        return await self.make_app()

    async def __aenter__(self):
        return await self.make_app()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
