from setuptools import setup, find_packages

setup(
    name='mayhemify',
    version='0.1.0',
    packages=find_packages(),
    package_dir={'mayhemify': 'mayhemify'},
    package_data={'mayhemify': ['templates/*']},
    include_package_data=True,
    install_requires=[
        'Click',
        'GitPython',
        'Jinja2',
        'requests',
        'giturlparse',
        'paramiko',
        'toml',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'mayhemify = mayhemify.scripts.mayhemify:cli',
        ],
    },
)
