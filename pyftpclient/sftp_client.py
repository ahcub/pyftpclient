import fnmatch
import stat
from logging import getLogger
from os.path import dirname, join

from os_utils.path import mkpath, delete
from paramiko import SSHClient, AutoAddPolicy

logger = getLogger('ftp_client.sftp')


class SFTPClient:
    def __init__(self, hostname, username=None, password=None, port=22, key_filename=None):
        self.host = hostname
        self.port = port
        self.user = username
        self.passwd = password
        self.key_filename = key_filename
        self.sftp = None
        self.ssh_client = None

    def connect(self):
        logger.info('Openning FTP connection to %s', self.host)
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(AutoAddPolicy())
        ssh_client.connect(hostname=self.host, port=self.port, username=self.user, password=self.passwd,
                           key_filename=self.key_filename)
        self.ssh_client = ssh_client
        self.sftp = self.ssh_client.open_sftp()

    def disconnect(self):
        self.sftp.close()
        self.ssh_client.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    def listdir(self, path):
        return self.sftp.listdir(path)

    def file_glob(self, path):
        dir_name = dirname(path)
        return fnmatch.filter(['/'.join([dir_name, filename]) for filename in self.sftp.listdir(dir_name)], path)

    def open(self, path, mode='r'):
        return self.sftp.open(path, mode=mode)

    def mkdir(self, dir_path):
        raise NotImplementedError()  # TODO: implement

    def delete(self, path):
        if self.exists(path):
            for file_attr in self.sftp.listdir_attr(path):
                full_file_path = '/'.join((path, file_attr.filename))
                if stat.S_ISDIR(file_attr.st_mode):
                    self.delete(full_file_path)
                else:
                    self.sftp.remove(full_file_path)
            self.sftp.rmdir(path)

    def copy_tree(self, src, dst):
        mkpath(dst)
        for fileattr in self.sftp.listdir_attr(src):
            src_path = '/'.join((src, fileattr.filename))
            dst_path = join(src, fileattr.filename)
            if stat.S_ISDIR(fileattr.st_mode):
                self.copy_tree(src_path, dst_path)
            else:
                delete(dst_path)
                self.sftp.get(src_path, dst_path)

    def exists(self, path):
        try:
            self.sftp.stat(path)
        except FileNotFoundError:
            return False
        else:
            return True
