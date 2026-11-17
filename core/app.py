"""Wires the engine, scheduler, server, native window and tray together.

Thread layout:
  * main thread    - pystray's system-tray message loop
  * scheduler      - one-second wall-clock tick
  * http thread(s) - the loopback control-panel server
  * app window     - chromeless Microsoft Edge --app window via window.py
"""
import threading
import webbrowser

from . import audio, scheduler, server, store, window

_state = {"settings": None, "schedule": None}
_engine = None
_sched = None
_httpd = None
_port = None
_icon = None
_use_window = False


def get_settings():
    return _state["settings"]


def get_schedule():
    return _state["schedule"]


def reload_from_disk():
    _state["settings"] = store.load_settings()
    _state["schedule"] = store.load_schedule()
    server.Api.settings = _state["settings"]
    server.Api.schedule = _state["schedule"]
    _refresh_tray()


# ---- tray ------------------------------------------------------------

def _make_image(colour):
    """Bell glyph drawn at runtime, so there is no binary asset to ship."""
    from PIL import Image, ImageDraw
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((6, 6, 58, 58), fill=colour)
    d.polygon([(32, 14), (46, 40), (18, 40)], fill="white")
    d.rectangle((14, 40, 50, 45), fill="white")
    d.ellipse((28, 46, 36, 54), fill="white")
    return img


def _title_text():
    s = _state["settings"] or {}
    name = s.get("school_name") or "Zil"
    if not s.get("enabled", True):
        return "%s - DURAKLATILDI" % name
    nxt = _sched.next_event() if _sched else None
    if nxt:
        return "%s - sıradaki %s %s" % (name, nxt["when"].strftime("%a %H:%M"), nxt["key"])
    return "%s - yaklaşan zil yok" % name


def _refresh_tray():
    if not _icon:
        return
    try:
        s = _state["settings"] or {}
        _icon.icon = _make_image("#d1453b" if not s.get("enabled", True) else "#2c3e50")
        _icon.title = _title_text()[:127]        # Windows tooltip limit
    except Exception:
        pass


def open_panel(*_a):
    target_url = server.url(_port)
    if _use_window and window.show(target_url):
        return
    webbrowser.open(target_url)


def _toggle_enabled(*_a):
    s = dict(_state["settings"])
    s["enabled"] = not s.get("enabled", True)
    store.save_settings(s)
    reload_from_disk()


def _stop_audio(*_a):
    _engine.stop_all()
    _refresh_tray()


def _quit(*_a):
    try:
        _engine.stop_all()
    except Exception:
        pass
    if _sched:
        _sched.stop()
    if _httpd:
        threading.Thread(target=_httpd.shutdown, daemon=True).start()
    if _icon:
        _icon.stop()
    if _use_window:
        window.destroy()                          # releases window.start()


def build_tray():
    import pystray
    from pystray import MenuItem as Item

    return pystray.Icon("zil", _make_image("#2c3e50"), "Zil", pystray.Menu(
        Item("Kontrol panelini aç", open_panel, default=True),
        Item("Tüm sesleri durdur", _stop_audio),
        pystray.Menu.SEPARATOR,
        Item("Zil sistemi aktif", _toggle_enabled,
             checked=lambda _i: bool((_state["settings"] or {}).get("enabled", True))),
        Item("Yapılandırmayı yeniden yükle", lambda *_a: reload_from_disk()),
        pystray.Menu.SEPARATOR,
        Item("Çıkış", _quit),
    ))


# ---- entry -----------------------------------------------------------

def main(show_panel=False, force_browser=False):
    global _engine, _sched, _httpd, _port, _icon, _use_window

    reload_from_disk()

    _engine = audio.AudioEngine(on_change=_refresh_tray)
    _sched = scheduler.Scheduler(_engine, get_settings, get_schedule,
                                 on_tick=_refresh_tray)

    _httpd, _port = server.start(int(_state["settings"].get("ui_port", 8765)))
    server.Api.engine = _engine
    server.Api.scheduler = _sched
    server.Api.reload_cb = reload_from_disk

    _sched.start()

    _use_window = window.available() and not force_browser
    store.log_event("system", "start", "start",
                    "port %d, ui=%s" % (_port, "window" if _use_window else "browser"))

    _icon = build_tray()
    _refresh_tray()

    if show_panel:
        t = threading.Timer(0.2, open_panel)
        t.daemon = True
        t.start()
    _icon.run()                                   # blocks until _quit()

    store.log_event("system", "stop", "stop", "exited")
    return 0
