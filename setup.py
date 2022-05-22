from setuptools import setup
import sixe_idp

setup(
    name='6estates-idp',
    version=sixe_idp.__version__,
    description='Python SDK for IDP API by 6Estates Pte Ltd',
    long_description="""
6Estates IDP SDK
==================

Read more on https://idp-sdk-doc.nextcenter.net/python/
    
    """,
    author='guosihan',
    author_email='sihan.6estates@gmail.com',
    url="https://gitlab.6estates.com/algorithm/idp-python-sdk",
    license='BSD 2-clause',
    packages=['sixe_idp'],
    install_requires=['requests'],

    classifiers=[
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)