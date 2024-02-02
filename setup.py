from setuptools import setup
setup(
    name='MangaSplitter',
    version='0.0.1',
    entry_points={
        'console_scripts': [
            'manga_split = manga_split:main'
        ]
    }
)