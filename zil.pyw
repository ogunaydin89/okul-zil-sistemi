"""Zil - school bell system. Tray entry point.

Launched with pythonw.exe there is no console window. A single-instance lock
stops a second copy from ringing every bell twice.

  zil.pyw              start in the tray, window hidden
  zil.pyw --panel      start with the control panel window open
  zil.pyw --browser    fall back to the browser instead of a native window
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "lib"))     # vendored deps

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")


def _single_instance():
    """Windows named mutex: returns the handle, or None if already running."""
    try:
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateMutexW.restype = wintypes.HANDLE
        handle = k32.CreateMutexW(None, True, "Global\\ZilSchoolBellSystem")
        if ctypes.get_last_error() == 183:        # ERROR_ALREADY_EXISTS
            return None
        return handle
    except Exception:
        return True                                # never block startup over this


def main():
    if _single_instance() is None:
        if "--browser" in sys.argv or "--panel" in sys.argv:
            import webbrowser
            from core import store, window
            port = int(store.load_settings().get("ui_port", 8765))
            u = f"http://127.0.0.1:{port}/"
            if "--browser" in sys.argv:
                webbrowser.open(u)
            elif not window.show(u):
                webbrowser.open(u)
        return 0

    from core import app
    return app.main(show_panel="--panel" in sys.argv,
                    force_browser="--browser" in sys.argv)


if __name__ == "__main__":
    sys.exit(main())
