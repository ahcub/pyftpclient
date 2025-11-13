"""Base classes for FTP/SFTP client implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod
from ftplib import FTP
from pathlib import Path
from typing import Self

from paramiko.sftp_client import SFTPClient as ParamikoSFTPClient


class FTPClientBaseError(Exception):
    """Base exception for FTP client errors."""


class FTPClientBase(ABC):
    """Abstract base class for FTP and SFTP clients."""

    def __init__(
        self,
        hostname: str,
        username: str | None,
        password: str | None,
        port: int = 22,
    ) -> None:
        """Initialize FTP client base.

        Args:
            hostname: The hostname or IP address of the FTP server.
            username: The username for authentication.
            password: The password for authentication.
            port: The port number (default: 22 for SFTP, 21 for FTP).

        """
        self.host = hostname
        self.port = port
        self.user = username
        self.passwd = password
        self.ftp: FTP | ParamikoSFTPClient | None = None

    def __enter__(self) -> Self:
        """Enter context manager."""
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        """Exit context manager."""
        self.disconnect()

    @abstractmethod
    def connect(self) -> None:
        """Connect to the FTP server."""

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the FTP server."""

    @abstractmethod
    def isdir(self, _path: str) -> bool:
        """Check if path is a directory."""

    @abstractmethod
    def isfile(self, _path: str) -> bool:
        """Check if path is a file."""

    def copy_tree(self, src: str, dst: str, copy_type: str = "auto") -> None:
        """Copy a directory tree.

        Args:
            src: Source path.
            dst: Destination path.
            copy_type: Direction of copy - 'up', 'down', or 'auto'.

        """
        if copy_type == "auto":
            copy_type = "up" if Path(src).exists() else "down"

        if copy_type == "down":
            self.download_tree(src, dst)
        else:
            self.upload_tree(src, dst)

    @abstractmethod
    def download_tree(self, src: str, dst: str) -> None:
        """Download a directory tree from the server."""

    @abstractmethod
    def upload_tree(self, src: str, dst: str) -> None:
        """Upload a directory tree to the server."""

    def copy_file(self, src: str, dst: str, copy_type: str = "auto") -> None:
        """Copy a file.

        Args:
            src: Source path.
            dst: Destination path.
            copy_type: Direction of copy - 'up', 'down', or 'auto'.

        """
        if copy_type == "auto":
            copy_type = "up" if Path(src).exists() else "down"

        if copy_type == "down":
            self.download_file(src, dst)
        else:
            self.upload_file(src, dst)

    @abstractmethod
    def download_file(self, src: str, dst: str) -> None:
        """Download a file from the server."""

    @abstractmethod
    def upload_file(self, src: str, dst: str) -> None:
        """Upload a file to the server."""
