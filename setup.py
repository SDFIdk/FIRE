from setuptools import setup, find_packages


setup(name='fire-gama',
      version='0.0.2',
      description=u"Gama Export/import plugin for fire-cli",
      long_description="",
      classifiers=[],
      keywords='',
      author=u"Klavs Pihlkjær",
      author_email='klavs@septima.dk',
      url='https://github.com/Septima/fire-gama',
      license='MIT',
      packages=find_packages(exclude=['test']),
      include_package_data=True,
      zip_safe=False,
      install_requires=["click", "fire-cli"],
      entry_points="""
      [firecli.fire_commands]
      gama=firegama.cli:gama
      """
      )