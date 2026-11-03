"""Deferred imports for heavy libraries that students never need.

PyMuPDF, Pillow and NumPy are only used by admin PDF processing, image repair
and photo upload. Importing them at startup costs seconds of CPU on a 0.1 vCPU
instance, so the real module is loaded on first attribute access instead.
"""
import importlib
import threading


class LazyModule:
    def __init__(self, name):
        self._name = name
        self._module = None
        self._lock = threading.Lock()

    def _load(self):
        if self._module is None:
            with self._lock:
                if self._module is None:
                    self._module = importlib.import_module(self._name)
        return self._module

    def __getattr__(self, attr):
        return getattr(self._load(), attr)


fitz = LazyModule('fitz')
np = LazyModule('numpy')
PIL_Image = LazyModule('PIL.Image')
