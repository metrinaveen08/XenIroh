import os
import shutil
import stat
from datetime import datetime
from config.settings import getConfigDir


def getQuarantineDir():
    path = os.path.join(getConfigDir(), "Quarantine")
    os.makedirs(path, exist_ok=True)
    return path


def getProtectedPaths(watchedPaths):
    paths = list(watchedPaths)
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    if os.path.isdir(downloads):
        paths.append(downloads)
    seen = set()
    return [p for p in paths if os.path.isdir(p) and not (os.path.normcase(p) in seen or seen.add(os.path.normcase(p)))]


def quarantineFile(path):
    if not os.path.isfile(path):
        return None
    baseName = os.path.basename(path)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    destination = os.path.join(getQuarantineDir(), f"{stamp}_{baseName}")
    shutil.move(path, destination)
    try:
        os.chmod(destination, stat.S_IREAD)
    except OSError:
        pass
    return destination


def clearQuarantine():
    d = getQuarantineDir()
    for entry in os.scandir(d):
        if entry.is_file(follow_symlinks=False):
            try:
                os.chmod(entry.path, stat.S_IWRITE)
            except OSError:
                pass
            os.remove(entry.path)
        elif entry.is_dir(follow_symlinks=False):
            shutil.rmtree(entry.path)
