import fnmatch
import stat
from logging import getLogger
from os import listdir
from os.path import dirname, isdir, isfile, join, basename, getsize

from os_utils.path import delete, mkpath
from paramiko import AutoAddPolicy, SSHClient

from pyftpclient.client_base import FTPClientBase, FTPClientBaseError

logger = getLogger('ftp_client.sftp')


class SFTPClientError(FTPClientBaseError):
    pass


class SFTPClient(FTPClientBase):

    def isdir(self, _path):
        _stat = self.ftp.stat(_path).st_mode
        return stat.S_ISDIR(_stat)

    def isfile(self, _path):
        _stat = self.ftp.stat(_path).st_mode
        return stat.S_ISREG(_stat)

    def __init__(self, hostname, username=None, password=None, port=22, key_filename=None):
        super(SFTPClient, self).__init__(hostname, username, password, port)
        self.key_filename = key_filename
        self.ssh_client = None

    def connect(self):
        logger.info('Openning FTP connection to %s', self.host)
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.connect(hostname=self.host, port=self.port, username=self.user, password=self.passwd,
                           key_filename=self.key_filename)
        self.ssh_client = ssh_client
        self.ftp = self.ssh_client.open_sftp()

    def disconnect(self):
        self.ftp.close()
        self.ssh_client.close()

    def listdir(self, path):
        return self.ftp.listdir(path)

    def file_glob(self, path):
        dir_name = dirname(path)
        if self.exists(dir_name):
            return fnmatch.filter(['/'.join([dir_name, filename]) for filename in self.ftp.listdir(dir_name)], path)
        else:
            return []

    def open(self, path, mode='r'):
        return self.ftp.open(path, mode=mode)

    def mkdir(self, dir_path):
        try:
            self.ftp.stat(dir_path)
        except FileNotFoundError:
            self.mkdir(dirname(dir_path.rstrip('/')))
            self.ftp.mkdir(dir_path.rstrip('/'))

    def delete(self, path):
        try:
            if stat.S_ISDIR(self.ftp.stat(path).st_mode):
                for file_name in self.ftp.listdir(path):
                    full_file_path = '/'.join((path, file_name))
                    self.delete(full_file_path)
                self.ftp.rmdir(path)
            else:
                self.ftp.remove(path)
        except FileNotFoundError:
            pass

    def upload_tree(self, src, dst):
        if isfile(src):
            self.upload_file(src, dst)
        elif isdir(src):
            self.mkdir(dst)
            for sub_path in listdir(src):
                self.upload_tree(join(src, sub_path), '/'.join((dst, sub_path)))
        else:
            raise SFTPClientError('SFTP client supports only files and directories on upload operation')

    def download_tree(self, src, dst):
        mkpath(dst)
        for fileattr in self.ftp.listdir_attr(src):
            src_path = '/'.join((src, fileattr.filename))
            dst_path = join(dst, fileattr.filename)
            if stat.S_ISDIR(fileattr.st_mode):
                self.download_tree(src_path, dst_path)
            else:
                self.download_file(src_path, dst_path)

    def download_file(self, src, dst):
        if dst.endswith('/') or isdir(dst):
            dst = join(dst, basename(src))
        delete(dst)
        self.ftp.get(src, dst)
        src_size = self.file_size(src)
        dst_size = getsize(dst)
        if src_size != dst_size:
            raise SFTPClientError('source and destination size mismatch after copy, '
                                  'src: {} vs dst: {}'.format(src_size, dst_size))

    def upload_file(self, src, dst):
        self.ftp.put(src, dst)

    def file_size(self, path, bytes_magnitude=0):
        """
        :param bytes_magnitude: 0-bytes, 1-Kb, 2-Mb, 3-Gb
        """
        stat = self.ftp.stat(path)
        if bytes_magnitude == 0:
            return stat.st_size
        return stat.st_size / 1024**bytes_magnitude

    def exists(self, path):
        try:
            self.ftp.stat(path)
        except FileNotFoundError:
            return False
        else:
            return True
