"""Native application window hosting the control panel via Microsoft Edge.

Launches the Microsoft-signed Edge binary in chromeless ``--app`` mode so the
UI opens in its own app window (no address bar or browser tabs) without loading
unsigned third-party .NET/pythonnet DLLs that trigger Windows Smart App Control.

Closing the window leaves the tray engine running; only tray -> Çıkış exits.
"""
import os
import subprocess

WINDOW_TITLE_MARKER = "Zil — Okul Zil ve Tören Sistemi"

_BROWSER_CANDIDATES = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"%LocalAppData%\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
)


def _find_browser():
    """Return the path of the first installed Chromium-based app host, or None."""
    for raw in _BROWSER_CANDIDATES:
        path = os.path.expandvars(raw)
        if os.path.isfile(path):
            return path
    return None


def available():
    """True if a native app-mode browser host is installed on this machine."""
    return bool(_find_browser())


def _matching_hwnds():
    """Return visible window handles belonging to Zil's chromeless app window."""
    if os.name != "nt":
        return []
    try:
        import ctypes
        from ctypes import wintypes

        u32 = ctypes.WinDLL("user32", use_last_error=True)
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        u32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
        u32.EnumWindows.restype = wintypes.BOOL
        u32.IsWindowVisible.argtypes = [wintypes.HWND]
        u32.IsWindowVisible.restype = wintypes.BOOL
        u32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        u32.GetClassNameW.restype = ctypes.c_int
        u32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        u32.GetWindowTextLengthW.restype = ctypes.c_int
        u32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
        u32.GetWindowTextW.restype = ctypes.c_int

        handles = []
        cls_buf = ctypes.create_unicode_buffer(64)

        def _enum_cb(hwnd, _lparam):
            if not u32.IsWindowVisible(hwnd):
                return True
            cls_len = u32.GetClassNameW(hwnd, cls_buf, len(cls_buf))
            if cls_len <= 0 or cls_buf.value != "Chrome_WidgetWin_1":
                return True
            tlen = u32.GetWindowTextLengthW(hwnd)
            if tlen <= 0:
                return True
            tbuf = ctypes.create_unicode_buffer(tlen + 1)
            u32.GetWindowTextW(hwnd, tbuf, tlen + 1)
            if WINDOW_TITLE_MARKER in tbuf.value:
                handles.append(hwnd)
            return True

        cb = WNDENUMPROC(_enum_cb)
        u32.EnumWindows(cb, 0)
        return handles
    except Exception:
        return []


def focus_existing():
    """Bring an already-open Zil app window to the foreground, if found."""
    handles = _matching_hwnds()
    if not handles:
        return False
    try:
        import ctypes
        from ctypes import wintypes

        u32 = ctypes.WinDLL("user32", use_last_error=True)
        u32.IsIconic.argtypes = [wintypes.HWND]
        u32.IsIconic.restype = wintypes.BOOL
        u32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
        u32.ShowWindow.restype = wintypes.BOOL
        u32.SetForegroundWindow.argtypes = [wintypes.HWND]
        u32.SetForegroundWindow.restype = wintypes.BOOL

        hwnd = handles[0]
        if u32.IsIconic(hwnd):
            u32.ShowWindow(hwnd, 9)  # SW_RESTORE
        u32.SetForegroundWindow(hwnd)
        return True
    except Exception:
        return False


def show(url):
    """Focus an existing Zil app window or launch a new chromeless Edge --app window."""
    if focus_existing():
        return True
    browser = _find_browser()
    if not browser:
        return False
    sep = "&" if "?" in url else "?"
    app_url = f"{url}{sep}app=1"
    try:
        kwargs = {"close_fds": True}
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen([browser, f"--app={app_url}", "--window-size=1120,860"], **kwargs)
        return True
    except Exception:
        return False


def destroy():
    """Close only Zil's chromeless app window(s) via WM_CLOSE on exit."""
    handles = _matching_hwnds()
    if not handles:
        return
    try:
        import ctypes
        from ctypes import wintypes

        u32 = ctypes.WinDLL("user32", use_last_error=True)
        u32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        u32.PostMessageW.restype = wintypes.BOOL
        for hwnd in handles:
            u32.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
    except Exception:
        pass
