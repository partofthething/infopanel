from setuptools import setup, find_packages

with open('README.rst') as f:
    long_description = f.read()

required = ['Pillow>=3.1.2',
            'voluptuous>=0.9.3',
            'PyYAML>=3.11',
            'matplotlib>=1.0',
            'paho-mqtt==1.1',
            'pytest',
            'pydocstyle']

setup(name='infopanel',
    version='0.1',
    description='Live data and simple animation rendering for little display panels.',
    author='Nick Touran',
    author_email='infopanel@partofthething.com',
    url='https://github.com/partofthething/infopanel',
    packages=find_packages(),
    license='GPL',
    long_description=long_description,
    install_requires=required,
    keywords='monitoring mqtt animation led rgb matrix',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Developers',
        'Topic :: Multimedia :: Graphics',
        'Topic :: System :: Monitoring',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        ],
      test_suite='tests',
      include_package_data=True
     )
