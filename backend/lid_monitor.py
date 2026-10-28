import ctypes
import threading
import uuid

from ctypes import wintypes


# =========================================================
# CONSTANTES WINDOWS
# =========================================================

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

WM_POWERBROADCAST = 0x0218
PBT_POWERSETTINGCHANGE = 0x8013

DEVICE_NOTIFY_WINDOW_HANDLE = 0x00000000

GUID_LIDSWITCH_STATE_CHANGE = (
    "BA3E0F4D-B817-4094-A2D1-D56379E6A0F3"
)


# =========================================================
# STRUCTURES WINDOWS
# =========================================================

class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", wintypes.BYTE * 8),
    ]


class POWERBROADCAST_SETTING(ctypes.Structure):
    _fields_ = [
        ("PowerSetting", GUID),
        ("DataLength", wintypes.DWORD),
        ("Data", wintypes.BYTE * 1),
    ]


# =========================================================
# VARIABLES DU MONITEUR
# =========================================================

_window_handle = None
_notification_handle = None

_window_thread = None
_stop_event = threading.Event()

_callback = None


# =========================================================
# TYPES DES FONCTIONS WINDOWS
# =========================================================

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


user32.DefWindowProcW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]

user32.DefWindowProcW.restype = ctypes.c_ssize_t


user32.RegisterPowerSettingNotification.argtypes = [
    wintypes.HWND,
    ctypes.POINTER(GUID),
    wintypes.DWORD,
]

user32.RegisterPowerSettingNotification.restype = wintypes.HANDLE


user32.UnregisterPowerSettingNotification.argtypes = [
    wintypes.HANDLE,
]

user32.UnregisterPowerSettingNotification.restype = wintypes.BOOL


user32.PostMessageW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]

user32.PostMessageW.restype = wintypes.BOOL


user32.RegisterClassW.argtypes = [
    ctypes.c_void_p,
]

user32.RegisterClassW.restype = wintypes.ATOM


user32.CreateWindowExW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.HMENU,
    wintypes.HINSTANCE,
    wintypes.LPVOID,
]

user32.CreateWindowExW.restype = wintypes.HWND


user32.DestroyWindow.argtypes = [
    wintypes.HWND,
]

user32.DestroyWindow.restype = wintypes.BOOL


user32.GetMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
]

user32.GetMessageW.restype = wintypes.BOOL


user32.TranslateMessage.argtypes = [
    ctypes.POINTER(wintypes.MSG),
]

user32.TranslateMessage.restype = wintypes.BOOL


user32.DispatchMessageW.argtypes = [
    ctypes.POINTER(wintypes.MSG),
]

user32.DispatchMessageW.restype = ctypes.c_ssize_t


kernel32.GetModuleHandleW.argtypes = [
    wintypes.LPCWSTR,
]

kernel32.GetModuleHandleW.restype = wintypes.HMODULE


# =========================================================
# CALLBACK WINDOWS
# =========================================================

@WNDPROC
def _window_proc(
    hwnd,
    message,
    wparam,
    lparam
):
    global _notification_handle

    # -----------------------------------------------------
    # ÉVÉNEMENT D'ALIMENTATION / CAPOT
    # -----------------------------------------------------

    if message == WM_POWERBROADCAST:

        if wparam == PBT_POWERSETTINGCHANGE:

            if lparam:

                try:

                    setting = ctypes.cast(
                        lparam,
                        ctypes.POINTER(
                            POWERBROADCAST_SETTING
                        )
                    ).contents

                    incoming_guid = str(
                        uuid.UUID(
                            bytes_le=bytes(
                                setting.PowerSetting
                            )
                        )
                    ).upper()

                    expected_guid = (
                        GUID_LIDSWITCH_STATE_CHANGE.upper()
                    )

                    if incoming_guid == expected_guid:

                        if setting.DataLength >= 1:

                            lid_state = int(
                                setting.Data[0]
                            )

                            if _callback is not None:

                                _callback(
                                    lid_state
                                )

                except Exception as error:

                    print(
                        "[LID MONITOR] "
                        f"Erreur événement : {error}"
                    )

        return 1

    # -----------------------------------------------------
    # FERMETURE DE LA FENÊTRE
    # -----------------------------------------------------

    if message == 0x0010:  # WM_CLOSE

        user32.DestroyWindow(
            hwnd
        )

        return 0

    # -----------------------------------------------------
    # DESTRUCTION
    # -----------------------------------------------------

    if message == 0x0002:  # WM_DESTROY

        # WM_QUIT
        ctypes.windll.user32.PostQuitMessage(
            0
        )

        return 0

    return user32.DefWindowProcW(
        hwnd,
        message,
        wparam,
        lparam
    )


# =========================================================
# BOUCLE WINDOWS
# =========================================================

def _monitor_loop():

    global _window_handle
    global _notification_handle

    try:

        class_name = (
            "Sleep_LidMonitor"
        )

        hinstance = (
            kernel32.GetModuleHandleW(
                None
            )
        )

        # -------------------------------------------------
        # CLASSE WINDOWS
        # -------------------------------------------------

        class WNDCLASS(ctypes.Structure):
            _fields_ = [
                ("style", wintypes.UINT),
                ("lpfnWndProc", ctypes.c_void_p),
                ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int),
                ("hInstance", wintypes.HINSTANCE),
                ("hIcon", wintypes.HICON),
                ("hCursor", wintypes.HANDLE),
                ("hbrBackground", wintypes.HBRUSH),
                ("lpszMenuName", wintypes.LPCWSTR),
                ("lpszClassName", wintypes.LPCWSTR),
            ]

        window_class = WNDCLASS()

        window_class.lpfnWndProc = (
            ctypes.cast(
                _window_proc,
                ctypes.c_void_p
            )
        )

        window_class.hInstance = (
            hinstance
        )

        window_class.lpszClassName = (
            class_name
        )

        user32.RegisterClassW(
            ctypes.byref(
                window_class
            )
        )

        # -------------------------------------------------
        # FENÊTRE INVISIBLE
        # -------------------------------------------------

        _window_handle = (
            user32.CreateWindowExW(
                0,
                class_name,
                "Sleep Lid Monitor",
                0,
                0,
                0,
                0,
                0,
                None,
                None,
                hinstance,
                None,
            )
        )

        if not _window_handle:

            raise RuntimeError(
                "Impossible de créer "
                "la fenêtre du moniteur."
            )

        # -------------------------------------------------
        # GUID DU CAPOT
        # -------------------------------------------------

        guid_bytes = uuid.UUID(
            GUID_LIDSWITCH_STATE_CHANGE
        ).bytes_le

        guid = GUID.from_buffer_copy(
            guid_bytes
        )

        # -------------------------------------------------
        # ENREGISTREMENT NOTIFICATION
        # -------------------------------------------------

        _notification_handle = (
            user32.RegisterPowerSettingNotification(
                _window_handle,
                ctypes.byref(guid),
                DEVICE_NOTIFY_WINDOW_HANDLE,
            )
        )

        if not _notification_handle:

            raise RuntimeError(
                "Impossible d'enregistrer "
                "la notification du capot."
            )

        print(
            "[LID MONITOR] "
            "Surveillance du capot active."
        )

        # -------------------------------------------------
        # BOUCLE DE MESSAGES
        # -------------------------------------------------

        message = wintypes.MSG()

        while not _stop_event.is_set():

            result = user32.GetMessageW(
                ctypes.byref(message),
                _window_handle,
                0,
                0
            )

            if result == 0:
                break

            if result == -1:
                break

            user32.TranslateMessage(
                ctypes.byref(message)
            )

            user32.DispatchMessageW(
                ctypes.byref(message)
            )

    except Exception as error:

        print(
            "[LID MONITOR] ❌",
            error
        )

    finally:

        # -------------------------------------------------
        # DÉSENREGISTREMENT
        # -------------------------------------------------

        if _notification_handle:

            try:

                user32.UnregisterPowerSettingNotification(
                    _notification_handle
                )

            except Exception:
                pass

            _notification_handle = None

        # -------------------------------------------------
        # DESTRUCTION FENÊTRE
        # -------------------------------------------------

        if _window_handle:

            try:

                user32.DestroyWindow(
                    _window_handle
                )

            except Exception:
                pass

            _window_handle = None

        print(
            "[LID MONITOR] "
            "Surveillance arrêtée."
        )


# =========================================================
# START
# =========================================================

def start(callback):

    global _callback
    global _window_thread

    if _window_thread is not None:
        return

    _callback = callback

    _stop_event.clear()

    _window_thread = threading.Thread(
        target=_monitor_loop,
        daemon=True,
        name="Sleep-LidMonitor"
    )

    _window_thread.start()


# =========================================================
# STOP
# =========================================================

def stop():

    global _window_thread

    if _window_thread is None:
        return

    print(
        "[LID MONITOR] "
        "Arrêt demandé..."
    )

    _stop_event.set()

    # -----------------------------------------------------
    # Réveiller la boucle GetMessageW
    #
    # IMPORTANT :
    # On ne transmet plus l'identifiant Python du thread
    # à une fonction Windows qui attend un type DWORD.
    # -----------------------------------------------------

    if _window_handle:

        try:

            user32.PostMessageW(
                _window_handle,
                0x0010,  # WM_CLOSE
                0,
                0
            )

        except Exception as error:

            print(
                "[LID MONITOR] "
                f"Erreur arrêt : {error}"
            )

    # -----------------------------------------------------
    # ATTENDRE LE THREAD
    # -----------------------------------------------------

    if _window_thread.is_alive():

        _window_thread.join(
            timeout=3
        )

    _window_thread = None

    _callback = None