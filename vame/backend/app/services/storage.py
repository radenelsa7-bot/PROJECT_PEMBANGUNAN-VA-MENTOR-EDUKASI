"""Abstraksi penyimpanan berkas (Issue #10).
Backend default: filesystem lokal. Antarmuka siap S3; implementasi S3 dapat ditambahkan tanpa mengubah pemakai."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class StorageABC(ABC):
    @abstractmethod
    def upload(self, source_path: str, dest_key: str) -> str:
        """Unggah berkas dari source_path ke dest_key; kembalikan lokasi tujuan."""

    @abstractmethod
    def download(self, dest_key: str, target_path: str) -> str:
        """Unduh dest_key ke target_path; kembalikan target_path."""

    @abstractmethod
    def url(self, key: str) -> str:
        """URL publik untuk mengakses key."""


class LocalStorage(StorageABC):
    def __init__(self, root: str = "storage"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def upload(self, source_path: str, dest_key: str) -> str:
        dst = self.root / dest_key
        dst.parent.mkdir(parents=True, exist_ok=True)
        Path(source_path).replace(dst)  # pindahkan ke storage
        return str(dst)

    def download(self, dest_key: str, target_path: str) -> str:
        src = self.root / dest_key
        Path(target_path).write_bytes(src.read_bytes())
        return target_path

    def url(self, key: str) -> str:
        return f"/storage/{key}"


def get_storage(backend: str = "local", root: str = "storage") -> StorageABC:
    if backend == "local":
        return LocalStorage(root)
    raise ValueError(f"Storage backend tidak didukung: {backend}")
