from setuptools import setup
from distutils.util import convert_path

main_ns = {}
ver_path = convert_path('titta/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

setup(
    name=main_ns['__title__'],
    version=main_ns['__version__'],
    author=main_ns['__author__'],
    author_email=main_ns['__email__'],
    description=main_ns['__description__'],
    long_description=main_ns['__description__'],
    long_description_content_type = 'text/plain',
    url=main_ns['__url__'],
    project_urls={
        "Source Code": main_ns['__url__'],
    },
    license=main_ns['__license__'],

    packages=['titta'],
    python_requires=">=3.8",
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering',
        'Topic :: Software Development :: Libraries',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Environment :: X11 Applications',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
    ],
    install_requires=['numpy','pandas','h5py','TittaPy','websocket_client'],
    long_description=open('README.md').read(),
)
