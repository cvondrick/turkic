from distutils.core import setup
from distutils.extension import Extension
from turkic.fileutil import getfiles

datafiles  = list(getfiles("turkic/skeleton"))
datafiles += list(getfiles("turkic/public"))
datafiles  = ["/".join(x.split("/")[1:]) for x in datafiles]

setup(
    name = "turkic",
    author = "Carl Vondrick",
    author_email = "cvondric@ics.uci.edu",
    description = "A framework for Mechanical Turk HITs",
    license = "MIT",
    version = "0.1.0",
    classifiers = ['Development Status :: 1 - Planning',
                   'Intended Audience :: Developers'],
    packages = ["turkic"],
    scripts = ['scripts/turkic'],
    package_dir = {"turkic": "turkic"},
    package_data = {"": datafiles}
)
