import setuptools

with open('requirements.txt') as f:
    required = f.read().splitlines()

setuptools.setup(
    name='Modicum',
    version='0.01',
    author='Scott Eisele',
    author_email='scott.r.eisele@vanderbilt.edu',
    maintainer='Modicum team',
    description='Mechanisms for an Outsourced Decentralized Computation Market',
    packages=['modicum'],
    include_package_data=True,
    install_requires=required,
    extras_require={
        'dotenv': ['python-dotenv']
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Ubuntu 18.04",
    ],
    entry_points={
        'console_scripts':[
            'modicum = modicum.cli:main',
        ],
    },
)
