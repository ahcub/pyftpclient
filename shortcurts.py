from ftp_client import FTPClient
from sftp_client import SFTPClient


class PyFTPClient(Exception):
    pass


def open_ftp(host, user=None, password=None, port=22, key_filename=None, ftp_type='ftp'):
    if ftp_type == 'ftp':
        return FTPClient(host, user, password, port)
    elif ftp_type == 'sftp':
        return SFTPClient(host, user, password, port, key_filename)
    else:
        raise PyFTPClient('Unknown ftp type: %s', ftp_type)
