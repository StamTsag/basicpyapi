from setuptools import setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name = 'basicpyapi',
    version = '0.1',
    description = 'A basic websocket server/client example.',
    long_description = long_description,
    long_description_content_type = 'text/markdown',
    author = 'Shadofer#7312',
    author_email = 'shadowrlrs@gmail.com',
    url = 'https://github.com/Shadofer/basicpyapi',
    packages = ['basicpyapi'],
    install_requires = ['websockets'],
    license = 'MIT'
)