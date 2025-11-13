"""Convenience functions for opening FTP/SFTP connections."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from pyftpclient.client_base import FTPClientBase

from pyftpclient.ftp_client import FTPClient
from pyftpclient.sftp_client import SFTPClient


class PyFTPClientError(Exception):
    """Error raised when opening FTP/SFTP connections."""


def open_ftp(  # noqa: PLR0913
    host: str,
    user: str | None = None,
    password: str | None = None,
    port: int = 22,
    key_filename: str | None = None,
    ftp_type: Literal["ftp", "sftp"] = "ftp",
) -> FTPClientBase:
    """Open an FTP or SFTP connection.

    Args:
        host: The hostname or IP address of the server.
        user: The username for authentication.
        password: The password for authentication.
        port: The port number (default: 22).
        key_filename: Path to SSH private key file (SFTP only).
        ftp_type: Type of connection - 'ftp' or 'sftp'.

    Returns:
        FTPClient or SFTPClient instance.

    Raises:
        PyFTPClientError: If ftp_type is not 'ftp' or 'sftp'.

    """
    if ftp_type == "ftp":
        return FTPClient(host, user, password, port)
    if ftp_type == "sftp":
        return SFTPClient(host, user, password, port, key_filename)
    msg = f"Unknown ftp type: {ftp_type}"
    raise PyFTPClientError(msg)
