import base64
import json
import os
import tempfile
import hashlib
from datetime import datetime, timezone

from config.settings import getConfigDir

try:
    from cryptography.fernet import Fernet, InvalidToken
    HAS_FERNET = True
except ImportError:
    HAS_FERNET = False
    class InvalidToken(Exception):
        pass

PUBLIC_RULES_FILENAME = "Rules.txt"
PRIVATE_RULES_FILENAME = "Rules.secret.dat"
KDF_ITERATIONS = 100_000


class RulesAuthenticationError(ValueError):
    pass


def getPublicRulesPath():
    return os.path.join(getConfigDir(), PUBLIC_RULES_FILENAME)


def getPrivateRulesPath():
    return os.path.join(getConfigDir(), PRIVATE_RULES_FILENAME)


def _derive_key(password, salt):
    if not password:
        raise RulesAuthenticationError("An access password is required.")
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        KDF_ITERATIONS
    )
    return base64.urlsafe_b64encode(key)


def _xor_cipher(data, key):
    out = bytearray(len(data))
    keyLen = len(key)
    for i in range(len(data)):
        out[i] = data[i] ^ key[i % keyLen]
    return bytes(out)


def _atomic_write(path, content, binary=False):
    d = os.path.dirname(path)
    fd, tempPath = tempfile.mkstemp(dir=d)
    try:
        if binary:
            with os.fdopen(fd, "wb") as h:
                h.write(content)
        else:
            with os.fdopen(fd, "w", encoding="utf-8") as h:
                h.write(content)
        os.replace(tempPath, path)
    except Exception:
        try:
            os.unlink(tempPath)
        except OSError:
            pass
        raise


def _hide_on_windows(path):
    if os.name != "nt":
        return
    try:
        import ctypes
        ctypes.windll.kernel32.SetFileAttributesW(path, 0x02)
    except Exception:
        pass


def _public_summary(policy):
    enabled = policy.get("enabledRules", [])
    lines = [
        "XenIroh protection summary",
        "=" * 28,
        "Shareable overview only. Detailed rules are encrypted.",
        "",
        f"Experience profile: {policy.get('experienceLabel', 'Not specified')}",
        f"Protection areas: {', '.join(policy.get('protectionAreas', [])) or 'Not specified'}",
        f"Enabled protections: {len(enabled)}",
        "",
        "Detailed rules require the developer access password selected during setup."
    ]
    return "\n".join(lines) + "\n"


def writePublicRules(policy):
    _atomic_write(getPublicRulesPath(), _public_summary(policy))


def initializeRules(policy, password, accessOwner="User"):
    salt = os.urandom(16)
    derived = _derive_key(password, salt)
    privatePolicy = dict(policy)
    privatePolicy.update({
        "version": 1,
        "accessOwner": accessOwner,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    })
    payload = json.dumps(privatePolicy, indent=2, sort_keys=True).encode("utf-8")

    if HAS_FERNET:
        token = Fernet(derived).encrypt(payload).decode("ascii")
        engine = "Fernet"
    else:
        encrypted = _xor_cipher(payload, derived)
        token = base64.b64encode(encrypted).decode("ascii")
        engine = "Builtin"

    envelope = {
        "version": 1,
        "engine": engine,
        "iterations": KDF_ITERATIONS,
        "salt": base64.b64encode(salt).decode("ascii"),
        "token": token,
    }
    _atomic_write(getPrivateRulesPath(), json.dumps(envelope, indent=2))
    _hide_on_windows(getPrivateRulesPath())
    writePublicRules(privatePolicy)


def loadPrivateRules(password):
    try:
        with open(getPrivateRulesPath(), "r", encoding="utf-8") as h:
            envelope = json.load(h)
        salt = base64.b64decode(envelope["salt"])
        token = envelope["token"]
        derived = _derive_key(password, salt)

        if envelope.get("engine") == "Fernet" and HAS_FERNET:
            content = Fernet(derived).decrypt(token.encode("ascii")).decode("utf-8")
        else:
            raw = base64.b64decode(token)
            content = _xor_cipher(raw, derived).decode("utf-8")

        return json.loads(content)
    except (OSError, KeyError, ValueError, InvalidToken, RulesAuthenticationError) as exc:
        raise RulesAuthenticationError("Password incorrect or rules file unreadable.") from exc


def savePrivateRules(policy, password):
    current = loadPrivateRules(password)
    current.update(policy)
    initializeRules(current, password, current.get("accessOwner", "User"))
