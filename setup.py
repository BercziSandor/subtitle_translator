"""
TODO
"""
import sys
from pathlib import Path

import setuptools

sys.path.append('.')

__description__ = "Subtitle translator"
__author__ = "SBerczi"
__copyright__ = "Copyright (c) 2022, SBerczi"
__credits__ = ["SBerczi"]
__license__ = "MIT"
__version__ = "0.0.1b1"
__maintainer__ = "SBerczi"
__email__ = "Berczi.Sandor@gmail.com"
__status__ = "4 - Beta"

README_PATH = Path(__file__).parent.absolute() / Path('README.md')
try:
    with open(README_PATH, 'r', encoding="UTF-8") as readme:
        __readme__ = readme.read()
except OSError as e:
    __readme__ = "Failed to read README.md!"

REQUIREMENTS_PATH = Path(__file__).parent.absolute() / Path('requirements.txt')
try:
    with open(REQUIREMENTS_PATH, 'r', encoding="UTF-8") as req:
        __requirements__ = [r.strip() for r in req.readlines()]
except OSError as e:
    __requirements__ = []

__doc__ = __readme__

setuptools.setup(
    name='subtitle_translator',
    packages=setuptools.find_packages(where='src'),
    package_dir={
            '': 'src',
        },
    # py_modules=['main'],

    long_description=__readme__,
    long_description_content_type='text/markdown',

    version=__version__,
    license=__license__,
    description=__description__,
    keywords=['subtitle', 'translate'],

    author=__author__,
    author_email=__email__,

    url='https://github.com/BercziSandor/subtitle_translator',

    install_requires=__requirements__,

    classifiers=[
        f'Development Status :: {__status__}',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
)
