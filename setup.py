from distutils.core import setup
from os.path import join, dirname

from setuptools import find_packages

with open(join(dirname(__file__), 'requirements.txt')) as requirements_file:
    install_reqs = [line.strip() for line in requirements_file]

print('install_reqs:', install_reqs)

with open('README.md') as file:
    long_description = file.read()

setup(
    name='pyftpclient',
    packages=find_packages(include=('pyftpclient',)),
    package_data={'': ['requirements.txt', 'LICENCE']},
    include_package_data=True,
    version='0.1.13',
    description='ftp client wrapper to simplify working with paramiko or ftplib',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Alex Buchkovsky',
    author_email='olex.buchkovsky@gmail.com',
    url='https://github.com/ahcub/pyftpclient',
    keywords=['wrapper', 'sftp', 'client', 'ftp'],
    install_requires=install_reqs,
)
