from setuptools import setup

with open('README.md') as f:
    readme = f.read()

with open('requirements.txt') as f:
    reqs = f.read()

setup(
    name='degiro',
    version='0.1.0',
    description='Basic unofficial python API for Degiro',
    long_description=readme,
    python_requires='>=3',
    py_modules=["degiro"],
    install_requires=reqs.strip().split('\n'),
)
