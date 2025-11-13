"""Python FTP/SFTP client library."""

from __future__ import annotations

__all__ = [
    "FTPClient",
    "FTPClientBase",
    "FTPClientBaseError",
    "FTPClientError",
    "PyFTPClientError",
    "SFTPClient",
    "SFTPClientError",
    "open_ftp",
]

from pyftpclient.client_base import FTPClientBase, FTPClientBaseError
from pyftpclient.ftp_client import FTPClient, FTPClientError
from pyftpclient.sftp_client import SFTPClient, SFTPClientError
from pyftpclient.shortcurts import PyFTPClientError, open_ftp
