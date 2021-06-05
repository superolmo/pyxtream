
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
     name='pyxtream',
     version='0.1',
     author="Claudio Olmi",
     author_email="superolmo2@gmail.com",
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
 )

