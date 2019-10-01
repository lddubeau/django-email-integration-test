import os

from setuptools import setup, find_packages

version = open("django_email_integration_test/VERSION").read().strip()
long_description = open("README.rst").read()

setup(
    name="django-email-integration-test",
    version=version,
    packages=find_packages(),
    author="Louis-Dominique Dubeau",
    author_email="ldd@lddubeau.com",
    description="Email integration test for Django.",
    long_description=long_description,
    license="MPL 2.0",
    keywords=["Django", "testing", "email"],
    url="https://github.com/lddubeau/django-email-integration-test",
    install_requires=[
        "Django>=2.2",
    ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Operating System :: POSIX",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
    ],
    include_package_data=True,
)
