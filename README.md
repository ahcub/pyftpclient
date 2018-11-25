FTP client wrapper
====================

pyftpclient is a library that is made to make work with FTP/SFTP simple. it has the common functions that you would use when working with a regular file system, like open a file listdir, and glob. It also has funcitons to simple download/upload of the files and directories from/to remote drive. The library takes care about opening and closing the sessions, so you don't have to worry about it


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
    sftp.download_file('/home/src_file'), '~/dst_file')
    sftp.download_tree(src_dir, dst_dir)
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
    ftp.download_file('/home/src_file'), '~/dst_file')
    ftp.download_tree(src_dir, dst_dir)
```