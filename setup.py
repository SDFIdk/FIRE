from setuptools import setup, find_packages


setup(name='fire-gama',
      version='0.0.1',
      description=u"Export and import fire data to/from gama",
      long_description="",
      classifiers=[],
      keywords='',
      author=u"Klavs Pihlkjær",
      author_email='klavs@septima.dk',
      url='www.septima.dk',
      license='Proprietary',
      packages=find_packages(exclude=['test']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'click'
      ],
      entry_points={
          'console_scripts': [
            'fire_gama=firegama.cli:cli'
        ]
          }
      )