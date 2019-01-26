from setuptools import setup, find_packages


setup(
    name = 'predigame',
    version = '1.2.13',
    description = 'An instructional game development platform',
    url = 'http://predigame.io',
    author = 'Predicate Academy',
    author_email = 'support@predigame.io',
    packages = find_packages(),
    install_requires = ['pygame', 'pillow', 'astar==0.9', 'PyGithub==1.38','bresenham==0.2'],
    include_package_data = True,
    entry_points = {
        'console_scripts': [
            'pred = predigame:bootstrap'
        ]
    }
)
