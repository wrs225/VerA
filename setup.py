from setuptools import setup, find_packages

setup(
    name='VerA',
    version='0.0.6',
    author='Will S, Sara A',
    author_email='wrs225@stanford.edu',
    description='A Python package for synthesizing and simulating fixed-point models of continuous systems.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)
