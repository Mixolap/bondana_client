from setuptools import setup, find_packages

with open("requirements.txt", "r") as f:
    install_requires = [line.strip() for line in f.readlines()]

setup(
    name='bondana_client',
    version='2024.11.19165247',
    packages=find_packages(),
    install_requires=install_requires,
    author='Mixolap',
    author_email='mixolapus@yandex.ru',
    description='Unofficial T-Bank wrapper',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/Mixolap/bondana_client',
    python_requires='>=3.5'
)
