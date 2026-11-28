"""Candado de máquina de Galivelop (RAG-3): un solo generador a la vez en la máquina.

Reimplementa el protocolo ``grun.lock/1`` (``galivelop-runtime/docs/protocol/grun.lock.1.md``) solo con stdlib,
sin importar ``grun``. El candado es un ``flock`` exclusivo sobre ``<estado>/gpu.lock``; el texto del archivo es
solo información.

- Ruta: ``$GALIVELOP_STATE_HOME`` (absoluta), si no ``$XDG_STATE_HOME/galivelop`` (absoluta), si no
  ``~/.local/state/galivelop``. Dentro de un Flatpak (``FLATPAK_ID``) un ``XDG_STATE_HOME`` que apunta al
  sandbox ``~/.var/app`` se ignora, como en ``grun/paths.py``.
- ``hold`` crea la carpeta y el archivo (modo 0600), sondea cada ``POLL_S`` con ``LOCK_EX | LOCK_NB`` y vence con
  ``LockBusyError``. Escribe el registro del titular de una línea en el sitio y lo trunca al soltar. Nunca borra
  ni sustituye el archivo (cambiaría el inodo y dos titulares tendrían candados sobre dos archivos).
- No poder abrir el archivo es ``LockUnavailableError``, nunca «libre». Sin ``fcntl`` (fuera de POSIX), error claro.
"""

import contextlib
import datetime
import json
import os
import time
from pathlib import Path

from gworld.rag import RagError

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None

POLL_S = 0.05
DEFAULT_TIMEOUT_S = 120.0
SCHEMA = "grun.lock/1"
APP = "gworld"
STATE_ENV = "GALIVELOP_STATE_HOME"


class MachineLockError(RagError):
    """Error base del candado de máquina."""


class LockBusyError(MachineLockError):
    """Otro proceso tiene el candado y se agotó el tiempo de espera."""


class LockUnavailableError(MachineLockError):
    """No se pudo abrir o usar el archivo del candado (no se toma nada)."""


def _xdg_base(name: str):
    base = os.environ.get(name)
    if not base or not os.path.isabs(base):
        return None
    if os.environ.get("FLATPAK_ID"):
        sandbox = Path.home() / ".var" / "app"
        if Path(base) == sandbox or sandbox in Path(base).parents:
            return None
    return Path(base)


def state_dir() -> Path:
    explicit = os.environ.get(STATE_ENV)
    if explicit and os.path.isabs(explicit):
        return Path(explicit)
    base = _xdg_base("XDG_STATE_HOME")
    if base is not None:
        return base / "galivelop"
    return Path.home() / ".local" / "state" / "galivelop"


def lock_path() -> Path:
    return state_dir() / "gpu.lock"


def _require_fcntl():
    if fcntl is None:
        raise MachineLockError(
            "el candado de máquina necesita fcntl (POSIX: Linux o macOS); en este sistema no está disponible")
    return fcntl


def _write_holder(fd: int, app, entry) -> None:
    """Registro del titular en el descriptor bloqueado, en el sitio. Mejor esfuerzo: el candado no depende de él."""
    record = {"schema": SCHEMA, "app": app, "pid": os.getpid(), "entry": entry,
              "since": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    try:
        os.ftruncate(fd, 0)
        os.lseek(fd, 0, os.SEEK_SET)
        os.write(fd, json.dumps(record).encode("utf-8"))
    except OSError:
        pass


@contextlib.contextmanager
def hold(timeout: float = DEFAULT_TIMEOUT_S, poll_s: float = POLL_S, *, app=APP, entry=None):
    """Toma el candado durante el bloque ``with``; espera hasta ``timeout`` segundos y vence con ``LockBusyError``."""
    lk = _require_fcntl()
    path = lock_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(path), os.O_RDWR | os.O_CREAT, 0o600)
    except OSError as exc:
        raise LockUnavailableError(f"no se puede abrir el candado {path}: {exc.strerror or exc}") from exc
    held = False
    try:
        deadline = time.monotonic() + timeout
        while True:
            try:
                lk.flock(fd, lk.LOCK_EX | lk.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise LockBusyError(
                        f"el candado de máquina {path} sigue ocupado tras {timeout:g} s") from None
                time.sleep(poll_s)
            except OSError as exc:
                raise LockUnavailableError(f"no se puede tomar el candado {path}: {exc.strerror or exc}") from exc
        held = True
        _write_holder(fd, app, entry)
        yield
    finally:
        if held:
            try:
                os.ftruncate(fd, 0)  # aún bloqueado: se vacía el registro antes de soltar
            except OSError:
                pass
        os.close(fd)  # cerrar suelta el candado


def busy():
    """``True`` si otro descriptor tiene el candado, ``False`` si está libre (o no hay archivo) y ``None`` si no se
    puede saber. No crea nada."""
    lk = _require_fcntl()
    try:
        fd = os.open(str(lock_path()), os.O_RDWR)
    except FileNotFoundError:
        return False
    except OSError:
        return None
    try:
        try:
            lk.flock(fd, lk.LOCK_SH | lk.LOCK_NB)
        except BlockingIOError:
            return True
        except OSError:
            return None
        return False
    finally:
        os.close(fd)


def holder():
    """``None`` si nadie lo tiene; el registro (dict) si está tomado, o ``{}`` si no hay un objeto JSON legible."""
    if busy() is not True:
        return None
    try:
        data = json.loads(lock_path().read_bytes().decode("utf-8"))
    except (OSError, ValueError, RecursionError):
        return {}
    return data if isinstance(data, dict) else {}
