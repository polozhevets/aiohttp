#! /usr/bin/env python
import asyncio
import aiohttp_jinja2
import aiohttp_debugtoolbar
import jinja2
from aiohttp_session import session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttp import web

from routes import routes
from middlewares import db_handler, authorize
from motor import motor_asyncio as ma
from settings import *


async def on_shutdown(app):
    for ws in app['websockets']:
        await ws.close(code=1001, message='Server shutdown')

middle = [
    session_middleware(EncryptedCookieStorage(SECRET_KEY)),
    authorize,
    db_handler,
]

if DEBUG:
    middle.append(aiohttp_debugtoolbar.middleware)

app = web.Application(
    # loop=loop,
    middlewares=middle)
if DEBUG:
    aiohttp_debugtoolbar.setup(app)
aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('templates'))

# route part
for route in routes:
    app.router.add_route(route[0], route[1], route[2], name=route[3])
app.router.add_static('/static', 'static', name='static')
# end route part
# db connect
app.client = ma.AsyncIOMotorClient(MONGO_HOST)
app.db = app.client[MONGO_DB_NAME]
# end db connect
app.on_cleanup.append(on_shutdown)
app['websockets'] = []

log.debug('start server')
web.run_app(app)
log.debug('Stop server end')
