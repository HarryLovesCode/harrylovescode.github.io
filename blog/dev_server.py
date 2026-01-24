import asyncio
import os
import signal

from aiohttp import web
from watchfiles import awatch

RELOAD_SCRIPT = """
<script>
  (function () {
    async function applyUpdate() {
      try {
        const res = await fetch(location.href, { cache: "no-store" });
        const text = await res.text();
        const doc = new DOMParser().parseFromString(text, "text/html");

        const newContent = doc.querySelector("#content");
        const oldContent = document.querySelector("#content");
        if (newContent && oldContent) {
          // Replace content
          oldContent.replaceWith(newContent);

          if (window.mermaid && typeof renderMermaid === "function") {
            try {
              mermaidInitialized = false;
              renderMermaid();
            } catch (e) {
              console.error("renderMermaid error", e);
            }
          }
        } else {
          // Fallback to full reload
          location.reload();
        }

        const newTitle = doc.querySelector("title");
        if (newTitle) document.title = newTitle.textContent;
      } catch (e) {
        console.error("applyUpdate error", e);
        location.reload();
      }
    }

    try {
      const proto = location.protocol === "https:" ? "wss://" : "ws://";
      const ws = new WebSocket(proto + location.host + "/ws");
      ws.onmessage = () => {
        applyUpdate();
      };
      ws.onclose = () => {
        console.log("reload socket closed");
      };
    } catch (e) {
      console.error("live-reload error", e);
    }
  })();
</script>
"""


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    request.app["sockets"].add(ws)
    try:
        async for _ in ws:
            pass
    finally:
        request.app["sockets"].discard(ws)
    return ws


async def file_handler(request):
    rel_path = request.path
    if rel_path == "/" or rel_path == "":
        file_path = os.path.join("../build", "index.html")
    else:
        file_path = os.path.join("../build", rel_path.lstrip("/"))

    if os.path.isdir(file_path):
        file_path = os.path.join(file_path, "index.html")

    if file_path.endswith(".html"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except FileNotFoundError:
            raise web.HTTPNotFound()

        if "</body>" in text:
            text = text.replace("</body>", RELOAD_SCRIPT + "</body>")
        else:
            text = text + RELOAD_SCRIPT

        return web.Response(text=text, content_type="text/html")

    if not os.path.exists(file_path):
        raise web.HTTPNotFound()

    return web.FileResponse(path=file_path)


async def watch_and_reload(app, ssg_func, watch_paths):
    async for changes in awatch(*watch_paths):
        print("Changes detected:", changes)
        try:
            ssg_func()
        except Exception as e:
            print("Error running ssg():", e)

        # Broadcast reload to all connected websockets
        for ws in list(app["sockets"]):
            try:
                await ws.send_str("reload")
            except Exception:
                app["sockets"].discard(ws)


async def on_startup(app):
    app["sockets"] = set()


async def run_dev(ssg_func, host="127.0.0.1", port=8000, watch_paths=None):
    if watch_paths is None:
        watch_paths = ["static", "pages", "posts"]

    app = web.Application()
    app.on_startup.append(on_startup)
    app.router.add_get("/ws", websocket_handler)
    app.router.add_get("/{tail:.*}", file_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)

    watcher_task = asyncio.create_task(watch_and_reload(app, ssg_func, watch_paths))

    await site.start()
    print(f"Dev server serving ./blog at http://{host}:{port}")

    # Use an asyncio Event and signal handlers for graceful shutdown
    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()

    def _signal_handler():
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            # add_signal_handler may not be implemented on some platforms
            pass

    try:
        await shutdown_event.wait()
        print("Shutdown signal received, stopping dev server...")
    finally:
        # Cancel watcher and close websockets
        watcher_task.cancel()
        try:
            await watcher_task
        except asyncio.CancelledError:
            pass

        for ws in list(app.get("sockets", [])):
            try:
                await ws.close()
            except Exception:
                pass

        await runner.cleanup()
