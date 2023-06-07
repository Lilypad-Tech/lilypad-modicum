import setuptools

setuptools.setup(
    name='Modicum',
    version='0.01',
    author='Scott Eisele',
    author_email='scott.r.eisele@vanderbilt.edu',
    maintainer='Modicum team',
    description='Mechanisms for an Outsourced Decentralized Computation Market',
    packages=['modicum'],
    include_package_data=True,
    install_requires=[
          'click',
          'influxdb',
          'tqdm',
          'python-dotenv',
          'pycurl',
          'docker',
          'pyzmq',
          'Fabric3',
          'apscheduler',
          'antlr4-python3-runtime',
          'web3==6.4.0'
      ],
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
