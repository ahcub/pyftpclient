from abc import abstractmethod
from os.path import exists


class FTPClientBaseError(Exception):
    pass


class FTPClientBase:
    def __init__(self, hostname, username, password, port=22):
        self.host = hostname
        self.port = port
        self.user = username
        self.passwd = password
        self.ftp = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def isdir(self, _path):
        pass

    @abstractmethod
    def isfile(self, _path):
        pass

    def copy_tree(self, src, dst, copy_type='auto'):
        if copy_type == 'auto':
            copy_type = 'up' if exists(src) else 'down'

        if copy_type == 'down':
            self.download_tree(src, dst)
        else:
            self.upload_tree(src, dst)

    @abstractmethod
    def download_tree(self, src, dst):
        pass

    @abstractmethod
    def upload_tree(self, src, dst):
        pass

    def copy_file(self, src, dst, copy_type='auto'):
        if copy_type == 'auto':
            copy_type = 'up' if exists(src) else 'down'

        if copy_type == 'down':
            self.download_file(src, dst)
        else:
            self.upload_file(src, dst)

    @abstractmethod
    def download_file(self, src, dst):
        pass

    @abstractmethod
    def upload_file(self, src, dst):
        pass
