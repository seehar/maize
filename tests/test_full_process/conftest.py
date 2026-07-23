"""
Local mock HTTP server fixtures for integration tests.

Provides a real aiohttp.web server on localhost so tests can exercise the
full spider pipeline (start_requests -> download -> parse -> pipeline -> item)
without depending on external websites.
"""

import socket
from typing import TYPE_CHECKING

import pytest
from aiohttp import web

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Page templates
# ---------------------------------------------------------------------------

INDEX_HTML = """\
<!DOCTYPE html>
<html>
<head><title>Mock Index</title></head>
<body>
  <h1>Mock Search Engine</h1>
  <ul>
    <li class="hotsearch-item">
      <a href="/page/1"><span class="title-content-title">First Result</span></a>
    </li>
    <li class="hotsearch-item">
      <a href="/page/2"><span class="title-content-title">Second Result</span></a>
    </li>
    <li class="hotsearch-item">
      <a href="/page/3"><span class="title-content-title">Third Result</span></a>
    </li>
  </ul>
</body>
</html>
"""

PAGE_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head><title>Page {page_id}</title></head>
<body>
  <h1>Page {page_id}</h1>
  <p>Content for page {page_id}.</p>
  <span class="page-id">{page_id}</span>
</body>
</html>
"""

ERROR_500_HTML = "<html><body>500 Internal Server Error</body></html>"


# ---------------------------------------------------------------------------
# Server handlers
# ---------------------------------------------------------------------------


async def index_handler(_request: web.Request) -> web.Response:
    return web.Response(text=INDEX_HTML, content_type="text/html", status=200)


async def page_handler(request: web.Request) -> web.Response:
    page_id = request.match_info["page_id"]
    return web.Response(
        text=PAGE_HTML_TEMPLATE.format(page_id=page_id),
        content_type="text/html",
        status=200,
    )


async def error_handler(_request: web.Request) -> web.Response:
    return web.Response(text=ERROR_500_HTML, content_type="text/html", status=500)


async def json_handler(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "items": [{"id": 1}, {"id": 2}, {"id": 3}]})


async def echo_handler(request: web.Request) -> web.Response:
    """Echo back request method and body for testing POST requests."""
    body = await request.text()
    return web.json_response({"method": request.method, "body": body, "headers": dict(request.headers)})


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
async def mock_server():
    """Start a local aiohttp.web server and yield its base URL.

    Yields:
        str: Base URL like ``http://127.0.0.1:<port>``
    """
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_get("/index", index_handler)
    app.router.add_get("/page/{page_id}", page_handler)
    app.router.add_get("/error", error_handler)
    app.router.add_get("/json", json_handler)
    app.router.add_route("*", "/echo", echo_handler)

    port = _find_free_port()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()

    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    await runner.cleanup()
