#!/usr/bin/env python3
"""
Setup script for DEI Extractor package.

This script installs the DEI Extractor package and its dependencies.
"""

from setuptools import find_packages, setup

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt") as fh:
    requirements = [
        line.strip() for line in fh if line.strip() and not line.startswith("#")
    ]

setup(
    name="dei-extractor",
    version="3.0.0",
    author="DEI Extractor Team",
    author_email="team@dei-extractor.com",
    description=(
        "A comprehensive Python package for extracting and processing "
        "DEI PDF invoice data"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dei-extractor/dei-extractor",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "types-PyYAML>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dei-extract=dei_extractor.cli:main",
            "dei-filter=dei_extractor.core.filter:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
