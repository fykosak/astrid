from setuptools import setup, find_packages
import sys, os

version = '0.3.2'

setup(name='astrid',
      version=version,
      description="Minimalistic continous integration",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='Git build continous integration',
      author='Michal Koutn\xc3\xbd',
      author_email='michal@fykos.cz',
      url='',
      license='WTFPL',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'GitPython',
          'cherrypy'
      ],
      scripts=[
          'bin/astrid'
      ],
      package_dir={
          'astrid': 'astrid'
      },
      package_data={
          'astrid': ['templates/*', 'static/style.css']
      },
      data_files=[
          ('config', ['repos.ini.sample', 'config.ini.sample'])
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
