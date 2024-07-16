from setuptools import setup, find_packages

setup(
    name='exboard',
    version='1.0.4',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        # 在这里列出你的包依赖，比如：
        # 'numpy',
    ],
)
