
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
     name='pyxtream',
     version='0.1',
     scripts=['pyxtream.py'] ,
     author="Claudio Olmi",
     author_email="superolmo2@gmail.com",
     description="xtream IPTV loader",
     long_description=long_description,
     long_description_content_type="text/markdown",
     url="https://github.com/superolmo2/pyxtream",
     packages=find_packages(),
     license="GPL3",
     classifiers=[
         "Intended Audience :: Developers",
         "Programming Language :: Python :: 3",
         "License :: OSI Approved :: GPL3 License",
         "Operating System :: OS Independent",
     ],
 )

