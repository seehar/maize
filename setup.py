from os.path import dirname
from os.path import join
from sys import version_info

import setuptools


if version_info < (3, 10, 0):
    raise SystemExit("Sorry! maize requires python 3.10.0 or later.")

with open(join(dirname(__file__), "maize/VERSION"), "rb") as fh:
    version = fh.read().decode("ascii").strip()

with open("README.md", encoding="utf8") as fh:
    long_description = fh.read()

packages = setuptools.find_packages()

requires = [
    "parsel>=1.8.1",
    "aiohttp>=3.9.1",
    "httpx>=0.26.0",
    "ujson>=5.9.0",
    "aiomysql>=0.2.0",
]

rpa_requires = [
    "playwright",
]

all_requires = [] + rpa_requires

setuptools.setup(
    name="maize",
    version=version,
    author="seehar",
    license="MIT",
    author_email="seehar@qq.com",
    python_requires=">=3.10",
    description="一个强大易用的爬虫框架",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=requires,
    # extras_require={"all": all_requires, "render": render_requires},
    extras_require={"all": all_requires, "rpa": rpa_requires},
    entry_points={"console_scripts": ["maize = maize.commands.cmdline:execute"]},
    url="https://github.com/seehar/maize.git",
    packages=packages,
    include_package_data=True,
    classifiers=["Programming Language :: Python :: 3"],
)
