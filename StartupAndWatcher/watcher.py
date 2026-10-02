import os
import threading
import time

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    HAS_WATCHDOG = True
except ImportError:
    HAS_WATCHDOG = False

from Assets.Analyzers.FileAnalyzer import analyzeFile
from Assets.Analyzers.ImageAnalyzer import analyzeImage
from Assets.AiConnector.aibridge import callAiAgent

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}
IGNORED_SUFFIXES = (".crdownload", ".part", ".tmp", ".download")

STABLE_CHECK_INTERVAL = 0.5
STABLE_CHECK_MATCHES = 2


def waitUntilFileIsStable(path, timeoutSeconds=45):
    lastSize = -1
    stableCount = 0
    deadline = time.time() + timeoutSeconds

    while time.time() < deadline:
        try:
            if not os.path.exists(path):
                return False
            currentSize = os.path.getsize(path)
        except OSError:
            return False

        if currentSize == lastSize and currentSize > 0:
            stableCount += 1
            if stableCount >= STABLE_CHECK_MATCHES:
                return True
        else:
            stableCount = 0
            lastSize = currentSize

        time.sleep(STABLE_CHECK_INTERVAL)

    return os.path.exists(path)


class WorkerAnalyzer:
    def __init__(self, onResultCallback):
        self.onResultCallback = onResultCallback
        self.seenFiles = set()
        self.lock = threading.Lock()

    def process(self, path):
        if path.lower().endswith(IGNORED_SUFFIXES):
            return
        threading.Thread(target=self._run, args=(path,), daemon=True).start()

    def _run(self, path):
        if not waitUntilFileIsStable(path):
            return
        if not os.path.isfile(path):
            return

        with self.lock:
            try:
                sig = (path, os.path.getmtime(path), os.path.getsize(path))
            except OSError:
                return
            if sig in self.seenFiles:
                return
            self.seenFiles.add(sig)

        ext = os.path.splitext(path)[1].lower()
        if ext in IMAGE_EXTENSIONS:
            evidence = analyzeImage(path)
        else:
            evidence = analyzeFile(path)

        aiResult = callAiAgent(evidence)
        try:
            self.onResultCallback(path, evidence, aiResult)
        except Exception:
            pass


if HAS_WATCHDOG:
    class WatchdogHandler(FileSystemEventHandler):
        def __init__(self, worker):
            super().__init__()
            self.worker = worker

        def on_created(self, event):
            if not event.is_directory:
                self.worker.process(event.src_path)

        def on_moved(self, event):
            if not event.is_directory:
                self.worker.process(event.dest_path)


class PollingWatcherThread(threading.Thread):
    def __init__(self, paths, worker, interval=1.0):
        super().__init__(daemon=True)
        self.paths = paths
        self.worker = worker
        self.interval = interval
        self.stopEvent = threading.Event()
        self.known = set()
        self._seed()

    def _seed(self):
        for p in self.paths:
            if os.path.isdir(p):
                try:
                    for f in os.listdir(p):
                        self.known.add(os.path.join(p, f))
                except OSError:
                    pass

    def run(self):
        while not self.stopEvent.is_set():
            for folder in self.paths:
                if not os.path.isdir(folder):
                    continue
                try:
                    for f in os.listdir(folder):
                        full = os.path.join(folder, f)
                        if os.path.isfile(full) and full not in self.known:
                            self.known.add(full)
                            self.worker.process(full)
                except OSError:
                    pass
            self.stopEvent.wait(self.interval)

    def stop(self):
        self.stopEvent.set()


class FolderWatcher:
    def __init__(self, onResultCallback):
        self.onResultCallback = onResultCallback
        self.worker = WorkerAnalyzer(onResultCallback)
        self.observer = None
        self.pollingThread = None

    def start(self, watchedPaths):
        self.stop()
        validPaths = [p for p in watchedPaths if os.path.isdir(p)]
        if not validPaths:
            return

        if HAS_WATCHDOG:
            self.observer = Observer()
            handler = WatchdogHandler(self.worker)
            for p in validPaths:
                self.observer.schedule(handler, p, recursive=False)
            self.observer.start()
        else:
            self.pollingThread = PollingWatcherThread(validPaths, self.worker)
            self.pollingThread.start()

    def stop(self):
        if HAS_WATCHDOG and self.observer is not None:
            self.observer.stop()
            self.observer.join(timeout=3)
            self.observer = None
        elif self.pollingThread is not None:
            self.pollingThread.stop()
            self.pollingThread.join(timeout=3)
            self.pollingThread = None

    def isRunning(self):
        if HAS_WATCHDOG and self.observer is not None:
            return self.observer.is_alive()
        if self.pollingThread is not None:
            return self.pollingThread.is_alive()
        return False
