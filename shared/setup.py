"""Setup for shared package."""

from setuptools import setup

setup(
    name="incident-copilot-shared",
    version="1.0.0",
    packages=["shared"],
    package_dir={"shared": "."},
    install_requires=["pydantic>=2.0"],
)
