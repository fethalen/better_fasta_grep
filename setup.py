"Build script for setuptools"

from __future__ import absolute_import
from setuptools import setup, find_packages
from distutils.util import convert_path

with open("README.md", "r") as fh:
    LONG_DESCRIPTION = fh.read()

setup(
    name="better_fasta_grep",
    version="1.0.2",
    author="Felix Thalen, Clemens Mauksch",
    author_email="felix.thalen@uni-goettingen.de, clemens.mauksch@uni-goettingen.de",
    license="GPL 3",
    description="Grep-like tool for retrieving matching sequence records from a FASTA file",
    package_dir={"":"src"},
    packages=find_packages(where="src"),
    entry_points={"console_scripts": ["bfg = better_fasta_grep.bfg:entry", "better_fasta_grep = better_fasta_grep.bfg:entry"]},
    install_requires=[
        "setuptools>=30.3.0"
        "wheel"
        "setuptools_scm"
    ],
    python_requires='>=3.6',
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    url="https://github.com/fethalen/better_fasta_grep",
    keywords=["bioinformatics", "fasta", "grep", "regular-expressions",
                "bioinformatics-tool", "grep-like"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Bio-Informatics"
    ],         
)