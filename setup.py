from setuptools import setup, find_packages

setup(
    name='pythams',
    version='0.0.1',
    author='Will S, Sara A',
    author_email='wrs225@stanford.edu',
    description='Tools for defining mixed-signal systems in python',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)