import os
from setuptools import setup, find_packages

install_requires = [
    'botocore',
    'boto3==1.4.2'
]

setup(
    name='RedLeader',
    version='0.2.0',
    description='An automated EC2 & ECS deployment platform',
    author='Morgan McDermott',
    author_email='morganmcdermott@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
        ]
    },
    package_data={
        'redleader': [
            'redleader/resources/policies/*.policy'
        ],
    },
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ]
)
