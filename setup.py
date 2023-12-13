
from setuptools import setup, find_packages
from distutils.util import convert_path

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

main_ns = {}
ver_path = convert_path('pyxtream/version.py')
with open(ver_path, encoding='utf-8') as ver_file:
    exec(ver_file.read(), main_ns)

setup(
    name='pyxtream',
    version=main_ns['__version__'],
    author=main_ns['__author__'],
    author_email=main_ns['__author_email__'],
    description="xtream IPTV loader",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/superolmo/pyxtream",
    packages=find_packages(),
    license="GPL3",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Natural Language :: English"
    ],
    extras_require={
        "REST_API":  ["Flask>=1.1.2",],
    }
 )
