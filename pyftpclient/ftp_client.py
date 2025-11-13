"""FTP client implementation using ftplib."""

from __future__ import annotations

import fnmatch
from ftplib import FTP, error_perm, error_temp
from io import BytesIO, IOBase
from logging import getLogger
from pathlib import Path
from time import sleep
from typing import Any, Self

from os_utils.path import mkpath

from pyftpclient.client_base import FTPClientBase, FTPClientBaseError

logger = getLogger("ftp_client.ftp")


class FTPClientError(FTPClientBaseError):
    """FTP client specific errors."""


class FTPClient(FTPClientBase):
    """FTP client implementation using standard FTP protocol."""

    ftp: FTP | None  # Override base class type annotation

    def connect(self) -> None:
        """Connect to the FTP server."""
        logger.info("Opening FTP connection to %s", self.host)
        self.ftp = FTP()  # noqa: S321
        self.ftp.connect(self.host, self.port)
        self.ftp.login(user=self.user or "", passwd=self.passwd or "")

    def disconnect(self) -> None:
        """Disconnect from the FTP server."""
        assert self.ftp is not None, "Not connected to FTP server"
        self.ftp.quit()

    def listdir(self, path: str) -> list[str]:
        """List directory contents.

        Args:
            path: Directory path to list.

        Returns:
            List of filenames in the directory.

        """
        assert self.ftp is not None, "Not connected to FTP server"
        return [Path(dir_path).name for dir_path in self.ftp.nlst(path)]

    def file_glob(self, path: str) -> list[str]:
        """Find files matching a pattern.

        Args:
            path: Pattern to match.

        Returns:
            List of matching file paths.

        """
        assert self.ftp is not None, "Not connected to FTP server"
        dir_name = Path(path).parent
        if self.exists(str(dir_name)):
            return fnmatch.filter(self.ftp.nlst(str(dir_name)), path)
        return []

    def open(self, path: str, mode: str = "r") -> FTPFile:
        """Open a file on the FTP server.

        Args:
            path: File path to open.
            mode: File mode ('r', 'w', 'a').

        Returns:
            FTPFile object.

        """
        assert self.ftp is not None, "Not connected to FTP server"
        return FTPFile(self.ftp, path, mode).open()

    def mkdir(self, dir_path: str) -> None:
        """Create a directory on the FTP server.

        Args:
            dir_path: Directory path to create.

        """
        assert self.ftp is not None, "Not connected to FTP server"
        try:
            self.ftp.nlst(dir_path)
        except error_temp:
            try:
                self.mkdir(str(Path(dir_path.rstrip("/")).parent))
            except error_perm:
                logger.warning("failed to create a parent directory")
            self.ftp.mkd(dir_path.rstrip("/"))

    def delete(self, path: str) -> None:
        """Delete a file or directory on the FTP server.

        Args:
            path: Path to delete.

        """
        assert self.ftp is not None, "Not connected to FTP server"
        try:
            logger.debug("deleting path: %s", path)
            for sub_path in self.ftp.nlst(path):
                if sub_path == path:
                    logger.debug("deleting file: %s", path)
                    self.ftp.delete(sub_path)
                    return
                self.delete(sub_path)

            try:
                self.ftp.rmd(path)
            except error_perm:
                sleep(0.1)
                logger.warning("Failed to delete directory %s, retrying...", path)
                self.delete(path)
        except error_temp as error:
            logger.info("directory does not exist: %s", error)

    def download_tree(self, src: str, dst: str) -> None:
        """Download a directory tree from the FTP server.

        Args:
            src: Source directory path on the server.
            dst: Destination directory path locally.

        """
        assert self.ftp is not None, "Not connected to FTP server"
        for sub_path in self.ftp.nlst(src):
            if sub_path == src:
                self.download_file(src, dst)
            else:
                mkpath(dst)
                self.download_tree(sub_path, str(Path(dst) / Path(sub_path).name))

    def upload_tree(self, src: str, dst: str) -> None:
        """Upload a directory tree to the FTP server.

        Args:
            src: Source directory path locally.
            dst: Destination directory path on the server.

        """
        src_path = Path(src)
        if src_path.is_file():
            self.upload_file(src, dst)
        elif src_path.is_dir():
            self.mkdir(dst)
            for sub_path in src_path.iterdir():
                self.upload_tree(str(sub_path), f"{dst}/{sub_path.name}")
        else:
            msg = "FTP client supports only files and directories on upload operation"
            raise FTPClientError(msg)

    def download_file(self, src: str, dst: str) -> None:
        """Download a file from the FTP server.

        Args:
            src: Source file path on the server.
            dst: Destination file path locally.

        """
        assert self.ftp is not None, "Not connected to FTP server"
        dst_path = Path(dst)
        if dst.endswith("/") or dst_path.is_dir():
            dst_path = dst_path / Path(src).name
        with dst_path.open("wb") as dst_file:
            self.ftp.retrbinary(f"RETR {src}", dst_file.write)

    def upload_file(self, src: str, dst: str) -> None:
        """Upload a file to the FTP server.

        Args:
            src: Source file path locally.
            dst: Destination file path on the server.

        """
        assert self.ftp is not None, "Not connected to FTP server"
        with Path(src).open("rb") as src_file:
            self.ftp.storbinary(f"STOR {dst}", src_file)

    def exists(self, path: str) -> bool:
        """Check if a path exists on the FTP server.

        Args:
            path: Path to check.

        Returns:
            True if path exists, False otherwise.

        """
        assert self.ftp is not None, "Not connected to FTP server"
        try:
            self.ftp.nlst(path)
        except error_temp:
            return False
        else:
            return True

    def file_size(self, path: str, bytes_magnitude: int = 1) -> float:
        """Get file size.

        Args:
            path: File path.
            bytes_magnitude: 1-bytes, 2-Kb, 3-Mb, 4-Gb.

        Returns:
            File size in the specified magnitude.

        """
        assert self.ftp is not None, "Not connected to FTP server"
        size = self.ftp.size(path)
        if size is None:
            return 0.0
        return float(size / 1024**bytes_magnitude)

    def isdir(self, _path: str) -> bool:
        """Check if path is a directory.

        Args:
            _path: Path to check.

        Returns:
            True if path is a directory.

        """
        return not self.isfile(_path)

    def isfile(self, _path: str) -> bool:
        """Check if path is a file.

        Args:
            _path: Path to check.

        Returns:
            True if path is a file.

        """
        assert self.ftp is not None, "Not connected to FTP server"
        old = self.ftp.pwd()
        try:
            self.ftp.cwd(_path)
        except Exception as e:  # noqa: BLE001
            if "550" in str(e):
                return True
        finally:
            self.ftp.cwd(old)
        return False


class FTPFile(IOBase):
    """File-like object for FTP operations."""

    def __init__(self, ftp: FTP, path: str, mode: str) -> None:
        """Initialize FTP file.

        Args:
            ftp: FTP connection object.
            path: File path on the server.
            mode: File mode ('r', 'w', 'a').

        """
        super().__init__()
        self.ftp = ftp
        self.path = path
        self.mode = mode.removesuffix("b")
        self.b = BytesIO()
        # Delegate methods to BytesIO - use Any to avoid mypy method-assign errors
        self.read: Any = self.b.read
        self._seek: Any = self.b.seek
        self._readline: Any = self.b.readline
        self._readlines: Any = self.b.readlines
        self._fileno: Any = self.b.fileno
        self._truncate: Any = self.b.truncate

    def open(self) -> Self:
        """Open the file.

        Returns:
            Self for chaining.

        """
        if self.mode == "w":
            self.ftp.storbinary(f"STOR {self.path}", BytesIO())
        if self.mode == "r":
            self.ftp.retrbinary(f"RETR {self.path}", self.b.write)
            self.b.seek(0)
        return self

    def write(self, data_chunk: bytes | str) -> None:
        """Write data to the file.

        Args:
            data_chunk: Data to write.

        Raises:
            Exception: If file mode is not 'w' or 'a'.

        """
        if self.mode in ["w", "a"]:
            data = data_chunk if isinstance(data_chunk, bytes) else data_chunk.encode()
            self.ftp.storbinary(f"APPE {self.path}", BytesIO(data))
        else:
            msg = f'File mode must be "w" or "a" to write data, not "{self.mode}"'
            raise Exception(msg)  # noqa: TRY002

    def __enter__(self) -> Self:
        """Enter context manager.

        Returns:
            Self for chaining.

        """
        self.open()
        return self

    def __exit__(self, *args: object) -> None:
        """Exit context manager."""

    def seek(self, *args: Any, **kwargs: Any) -> Any:
        """Seek to position in file."""
        return self._seek(*args, **kwargs)

    def readline(self, *args: Any, **kwargs: Any) -> Any:
        """Read a line from the file."""
        return self._readline(*args, **kwargs)

    def readlines(self, *args: Any, **kwargs: Any) -> Any:
        """Read all lines from the file."""
        return self._readlines(*args, **kwargs)

    def fileno(self) -> Any:
        """Get file descriptor."""
        return self._fileno()

    def truncate(self, *args: Any, **kwargs: Any) -> Any:
        """Truncate the file."""
        return self._truncate(*args, **kwargs)
