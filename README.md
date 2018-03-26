FTP client wrapper
====================


SFTPClient example
```
from pyftpclient.sftp_client import SFTPClient

connection_config = {
    'hostname': '127.0.0.1',
    'username': 'viewonly',
    'password': 'viewonly'
}


with SFTPClient(**connection_config) as sftp:
    print(sftp.listdir('/')
```


FTPClient example
```
from pyftpclient.ftp_client import FTPClient

connection_config = {
    'hostname': '127.0.0.1',
    'username': 'viewonly',
    'password': 'viewonly'
    'port': 21
}


with FTPClient(**connection_config) as ftp:
    print(ftp.listdir('/')
```