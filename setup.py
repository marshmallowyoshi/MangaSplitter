from setuptools import setup
setup(
    name='manga_split',
    version='0.0.3',
    entry_points={
        'console_scripts': [
            'manga_split = manga_split:main'
        ]
    },
    package_dir={'': 'src'},
    packages=['manga_split']
)