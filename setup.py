from setuptools import setup

setup(
    name='Titta',
    url='https://github.com/marcus-nystrom/Titta',
    author='Marcus Nystrom',
    author_email='marcus.nystrom@humlab.lu.se',
    packages=['titta'],
    install_requires=['psychopy', 'websocket_client'],
    version='0.1',
    license='Creative Commons Attribution 4.0 (CC BY 4.0)',
    description='Titta is a toolbox for using eye trackers from Tobii with Python, specifically offering integration with PsychoPy',
    long_description=open('README.md').read(),
)