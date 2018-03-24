from setuptools import setup, find_packages

setup(
    name = 'predigame',
    version = '1.1.0',
    description = 'A Python based game development platform',
    url = 'http://predigame.io',
    author = 'Predicate Academy',
    author_email = 'support@predigame.io',
    packages = find_packages(),
    install_requires = ['pygame', 'pillow', 'astar'],
    include_package_data = True,
    entry_points = {
        'console_scripts': [
            'pred = predigame:main'
        ]
    }
)
