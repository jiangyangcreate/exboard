from setuptools import setup, find_packages

setup(
    name='exboard',
    version='1.0.8',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
    ],
)
