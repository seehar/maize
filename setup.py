
from os.path import dirname, join
from sys import version_info

import setuptools

if version_info < (3, 6, 0):
    raise SystemExit("Sorry! maize requires python 3.6.0 or later.")

with open(join(dirname(__file__), "maize/VERSION"), "rb") as fh:
    version = fh.read().decode("ascii").strip()

with open("README.md", "r", encoding="utf8") as fh:
    long_description = fh.read()

packages = setuptools.find_packages()
# packages.extend(
#     [
#         "feapder",
#         "feapder.templates",
#         "feapder.templates.project_template",
#         "feapder.templates.project_template.spiders",
#         "feapder.templates.project_template.items",
#     ]
# )

# requires = [
#     "better-exceptions>=0.2.2",
#     "DBUtils>=2.0",
#     "parsel>=1.5.2",
#     "PyMySQL>=0.9.3",
#     "redis>=2.10.6,<4.0.0",
#     "requests>=2.22.0",
#     "bs4>=0.0.1",
#     "ipython>=7.14.0",
#     "cryptography>=3.3.2",
#     "urllib3>=1.25.8",
#     "loguru>=0.5.3",
#     "influxdb>=5.3.1",
#     "pyperclip>=1.8.2",
#     "terminal-layout>=2.1.3",
# ]

# render_requires = [
#     "webdriver-manager>=4.0.0",
#     "playwright",
#     "selenium>=3.141.0",
# ]

# all_requires = [
#     "bitarray>=1.5.3",
#     "PyExecJS>=1.5.1",
#     "pymongo>=3.10.1",
#     "redis-py-cluster>=2.1.0",
# ] + render_requires

setuptools.setup(
    name="maize",
    version=version,
    author="seehar",
    license="MIT",
    author_email="seehar@qq.com",
    python_requires=">=3.6",
    description="maize是一个python工具包",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # install_requires=requires,
    # extras_require={"all": all_requires, "render": render_requires},
    entry_points={"console_scripts": ["maize = maize.commands.cmdline:execute"]},
    url="https://github.com/seehar/maize.git",
    packages=packages,
    include_package_data=True,
    classifiers=["Programming Language :: Python :: 3"],
)
