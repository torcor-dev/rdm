from setuptools import setup, find_packages

setup(
    name='rdm',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=False,
    install_requires=[
        'ffmpeg-python',
        'Pillow',
        'praw',
        'psycopg2',
        'pyaml',
        'PyYAML',
        'requests',
        ],
    entry_points={
        'console_scripts': [
            'rdm = rdm.manage:cli'
            ]
        }
    )


