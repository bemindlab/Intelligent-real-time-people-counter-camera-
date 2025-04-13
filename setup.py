#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup script for MANTA - Monitoring and Analytics Node for Tracking Activity
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("models/requirements.txt", "r", encoding="utf-8") as f:
    required = f.read().splitlines()

setup(
    name="manta-camera",
    version="0.1.0",
    author="BemindTech",
    author_email="info@bemind.tech",
    description="Person detection and tracking system for Raspberry Pi",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/BemindTech/bmt-manta-camera",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=required,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pre-commit>=3.0.0",
            "black>=23.3.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "flake8-docstrings>=1.7.0",
            "mypy>=1.3.0",
            "types-PyYAML>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "manta=camera.main:main",
        ],
    },
)