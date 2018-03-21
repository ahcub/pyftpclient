from distutils.core import setup

from setuptools import find_packages

setup(
    name='pyftpclient',
    packages=find_packages(include=('pyftpclient',)),
    version='0.0.2',
    description='ftp client wrapper to simplify working with paramiko or ftplib',
    author='Alex Buchkovsky',
    author_email='olex.buchkovsky@gmail.com',
    url='https://github.com/ahcub/pyftpclient',
    keywords=['wrapper', 'sftp', 'client', 'ftp'],
)
