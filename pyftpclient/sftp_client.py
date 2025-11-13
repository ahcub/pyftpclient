"""SFTP client implementation using paramiko."""

import fnmatch
import stat
from logging import getLogger
from os_utils.path import delete, mkpath
from paramiko import AutoAddPolicy, SSHClient
from paramiko.sftp_client import SFTPClient as ParamikoSFTPClient
from paramiko.sftp_file import SFTPFile
from pathlib import Path

from pyftpclient.client_base import FTPClientBase, FTPClientBaseError

logger = getLogger("ftp_client.sftp")


class SFTPClientError(FTPClientBaseError):
    """SFTP client specific errors."""


class SFTPClient(FTPClientBase):
    """SFTP client implementation using SSH/SFTP protocol."""

    def __init__(
        self,
        hostname: str,
        username: str | None = None,
        password: str | None = None,
        port: int = 22,
        key_filename: str | None = None,
    ) -> None:
        """Initialize SFTP client.

        Args:
            hostname: The hostname or IP address of the SFTP server.
            username: The username for authentication.
            password: The password for authentication.
            port: The port number (default: 22).
            key_filename: Path to SSH private key file.

        """
        super().__init__(hostname, username, password, port)
        self.key_filename = key_filename
        self.ssh_client: SSHClient | None = None
        self.ftp: ParamikoSFTPClient | None = None

    def isdir(self, _path: str) -> bool:
        """Check if path is a directory.

        Args:
            _path: Path to check.

        Returns:
            True if path is a directory.

        """
        assert self.ftp is not None, "Not connected to SFTP server"
        _stat = self.ftp.stat(_path).st_mode
        if _stat is None:
            return False
        return stat.S_ISDIR(_stat)

    def isfile(self, _path: str) -> bool:
        """Check if path is a file.

        Args:
            _path: Path to check.

        Returns:
            True if path is a file.

        """
        assert self.ftp is not None, "Not connected to SFTP server"
        _stat = self.ftp.stat(_path).st_mode
        if _stat is None:
            return False
        return stat.S_ISREG(_stat)

    def connect(self) -> None:
        """Connect to the SFTP server."""
        logger.info("Opening FTP connection to %s", self.host)
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.connect(
            hostname=self.host,
            port=self.port,
            username=self.user,
            password=self.passwd,
            key_filename=self.key_filename,
        )
        self.ssh_client = ssh_client
        self.ftp = self.ssh_client.open_sftp()

    def disconnect(self) -> None:
        """Disconnect from the SFTP server."""
        assert self.ftp is not None, "Not connected to SFTP server"
        assert self.ssh_client is not None, "SSH client not initialized"
        self.ftp.close()
        self.ssh_client.close()

    def listdir(self, path: str) -> list[str]:
        """List directory contents.

        Args:
            path: Directory path to list.

        Returns:
            List of filenames in the directory.

        """
        assert self.ftp is not None, "Not connected to SFTP server"
        result = self.ftp.listdir(path)
        return list(result)

    def file_glob(self, path: str) -> list[str]:
        """Find files matching a pattern.

        Args:
            path: Pattern to match.

        Returns:
            List of matching file paths.

        """
        assert self.ftp is not None, "Not connected to SFTP server"
        dir_name = Path(path).parent
        if self.exists(str(dir_name)):
            files = [f"{dir_name}/{filename}" for filename in self.ftp.listdir(str(dir_name))]
            return fnmatch.filter(files, path)
        return []

    def open(self, path: str, mode: str = "r") -> SFTPFile:
        """Open a file on the SFTP server.

        Args:
            path: File path to open.
            mode: File mode ('r', 'w', 'a').

        Returns:
            SFTPFile object.

        """
        assert self.ftp is not None, "Not connected to SFTP server"
        return self.ftp.open(path, mode=mode)

    def mkdir(self, dir_path: str) -> None:
        """Create a directory on the SFTP server.

        Args:
            dir_path: Directory path to create.

        """
        assert self.ftp is not None, "Not connected to SFTP server"
        try:
            self.ftp.stat(dir_path)
        except FileNotFoundError:
            self.mkdir(str(Path(dir_path.rstrip("/")).parent))
            self.ftp.mkdir(dir_path.rstrip("/"))

    def delete(self, path: str) -> None:
        """Delete a file or directory on the SFTP server.

        Args:
            path: Path to delete.

        """
        assert self.ftp is not None, "Not connected to SFTP server"
        try:
            st_mode = self.ftp.stat(path).st_mode
            if st_mode is not None and stat.S_ISDIR(st_mode):
                for file_name in self.ftp.listdir(path):
                    full_file_path = f"{path}/{file_name}"
                    self.delete(full_file_path)
                self.ftp.rmdir(path)
            else:
                self.ftp.remove(path)
        except FileNotFoundError:
            pass

    def upload_tree(self, src: str, dst: str) -> None:
        """Upload a directory tree to the SFTP server.

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
            msg = "SFTP client supports only files and directories on upload operation"
            raise SFTPClientError(msg)

    def download_tree(self, src: str, dst: str) -> None:
        """Download a directory tree from the SFTP server.

        Args:
            src: Source directory path on the server.
            dst: Destination directory path locally.

        """
        assert self.ftp is not None, "Not connected to SFTP server"
        mkpath(dst)
        for fileattr in self.ftp.listdir_attr(src):
            src_path = f"{src}/{fileattr.filename}"
            dst_path = str(Path(dst) / fileattr.filename)
            if fileattr.st_mode is not None and stat.S_ISDIR(fileattr.st_mode):
                self.download_tree(src_path, dst_path)
            else:
                self.download_file(src_path, dst_path)

    def download_file(self, src: str, dst: str) -> None:
        """Download a file from the SFTP server.

        Args:
            src: Source file path on the server.
            dst: Destination file path locally.

        """
        assert self.ftp is not None, "Not connected to SFTP server"
        dst_path = Path(dst)
        if dst.endswith("/") or dst_path.is_dir():
            dst_path = dst_path / Path(src).name
        delete(str(dst_path))
        self.ftp.get(src, str(dst_path))
        src_size = self.file_size(src)
        dst_size = dst_path.stat().st_size
        if src_size != dst_size:
            msg = (
                f"source and destination size mismatch after copy, "
                f"src: {src_size} vs dst: {dst_size}"
            )
            raise SFTPClientError(msg)

    def upload_file(self, src: str, dst: str) -> None:
        """Upload a file to the SFTP server.

        Args:
            src: Source file path locally.
            dst: Destination file path on the server.

        """
        assert self.ftp is not None, "Not connected to SFTP server"
        self.ftp.put(src, dst)

    def file_size(self, path: str, bytes_magnitude: int = 0) -> int | float:
        """Get file size.

        Args:
            path: File path.
            bytes_magnitude: 0-bytes, 1-Kb, 2-Mb, 3-Gb.

        Returns:
            File size in the specified magnitude.

        """
        assert self.ftp is not None, "Not connected to SFTP server"
        file_stat = self.ftp.stat(path)
        size = file_stat.st_size
        if size is None:
            return 0
        if bytes_magnitude == 0:
            return size
        return float(size / (1024**bytes_magnitude))

    def exists(self, path: str) -> bool:
        """Check if a path exists on the SFTP server.

        Args:
            path: Path to check.

        Returns:
            True if path exists, False otherwise.

        """
        assert self.ftp is not None, "Not connected to SFTP server"
        try:
            self.ftp.stat(path)
        except FileNotFoundError:
            return False
        else:
            return True
