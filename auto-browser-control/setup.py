#!/usr/bin/env python3
"""
Setup script for Auto-Browser-Control

Web automation library for browser control using Chrome Remote Debugging Protocol.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip() for line in f
            if line.strip() and not line.startswith('#')
        ]

setup(
    name="auto-browser-control",
    version="1.0.0",
    author="Auto-Browser-Control Team",
    author_email="team@auto-browser-control.dev",
    description="Web automation library for browser control using Chrome Remote Debugging Protocol",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gokipon/tools",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.9.0",
            "flake8>=6.0.0",
        ],
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=1.3.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "auto-browser-research=web_automation.scripts.daily_research:main",
        ],
    },
    include_package_data=True,
    package_data={
        "web_automation": [
            "*.md",
            "config/*.json",
            "scripts/*.py",
        ],
    },
    keywords=[
        "automation",
        "browser",
        "chrome",
        "selenium",
        "web-scraping",
        "obsidian",
        "research",
        "perplexity",
        "gmail",
        "github"
    ],
    project_urls={
        "Bug Reports": "https://github.com/gokipon/tools/issues",
        "Source": "https://github.com/gokipon/tools",
        "Documentation": "https://github.com/gokipon/tools/blob/main/auto-browser-control/README.md",
    },
    zip_safe=False,
)