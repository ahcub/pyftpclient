import fnmatch
from ftplib import FTP, error_temp, error_perm
from io import BytesIO, IOBase
from logging import getLogger
from os.path import basename, dirname, join
from time import sleep

from os_utils.path import mkpath

logger = getLogger('ftp_client.ftp')


class FTPClient:
    def __init__(self, host, user, password, port=22):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = password
        self.ftp = None

    def connect(self):
        logger.info('Openning FTP connection to %s', self.host)
        self.ftp = FTP()
        self.ftp.connect(self.host, self.port)
        self.ftp.login(user=self.user, passwd=self.passwd)

    def disconnect(self):
        self.ftp.quit()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    def listdir(self, path):
        return [basename(dir_path) for dir_path in self.ftp.nlst(path)]

    def file_glob(self, path):
        dir_name = dirname(path)
        return fnmatch.filter(self.ftp.nlst(dir_name), path)

    def open(self, path, mode='r'):
        return FTPFile(self.ftp, path, mode).open()

    def mkdir(self, dir_path):
        try:
            self.ftp.nlst(dir_path)
        except error_temp:
            self.mkdir(dirname(dir_path.rstrip('/')))
            self.ftp.mkd(dir_path.rstrip('/'))

    def delete(self, path):
        try:
            logger.debug('deleting path: %s', path)
            for sub_path in self.ftp.nlst(path):
                if sub_path == path:
                    logger.debug('deleting file: %s', path)
                    self.ftp.delete(sub_path)
                    return
                else:
                    self.delete(sub_path)

            try:
                self.ftp.rmd(path)
            except error_perm:
                sleep(0.1)
                logger.warning('Failed to delete directory %s, retrying...'.format(path))
                self.delete(path)
        except error_temp as error:
            logger.info('directory does not exist: %s', error)

    def copy_tree(self, src, dst):
        for sub_path in self.ftp.nlst(src):
            if sub_path == src:
                with open(dst, 'wb') as dst_file:
                    self.ftp.retrbinary('RETR {}'.format(sub_path), dst_file.write)
            else:
                mkpath(dst)
                self.copy_tree(sub_path, join(dst, basename(sub_path)))

    def exists(self, path):
        try:
            self.ftp.nlst(path)
            return True
        except error_temp:
            return False


class FTPFile(IOBase):
    def __init__(self, ftp, path, mode):
        self.ftp = ftp
        self.path = path
        self.mode = mode[:-1] if mode.endswith('b') else mode
        self.b = BytesIO()
        self.read = self.b.read
        self.seek = self.b.seek
        self.readline = self.b.readline
        self.readlines = self.b.readlines
        self.fileno = self.b.fileno
        self.truncate = self.b.truncate

        super(FTPFile, self).__init__()

    def open(self):
        if self.mode == 'w':
            self.ftp.storbinary('STOR {}'.format(self.path), BytesIO())
        if self.mode == 'r':
            self.ftp.retrbinary('RETR {}'.format(self.path), self.b.write)
            self.b.seek(0)
        return self

    def write(self, data_chunk):
        if self.mode in ['w', 'a']:
            self.ftp.storbinary('APPE {}'.format(self.path), BytesIO(data_chunk if isinstance(data_chunk, bytes) else data_chunk.encode()))
        else:
            raise Exception('File mode must be "w" or "a" to write data, not "{}"'.format(self.mode))

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        pass
