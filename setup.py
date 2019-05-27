from setuptools import setup, find_packages

from firemark import __version__ as plugin_version

setup(
    name="fire-mark",
    version=plugin_version,
    description="Mark file plugin for fire-cli",
    long_description="Mark file plugin for fire-cli",
    classifiers=[],
    keywords="",
    author=u"GRF / SDFE",
    author_email="grf@sdfe.dk",
    url="https://github.com/Kortforsyningen/fire-mark",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=["click", "fire-cli"],
    entry_points="""
      [firecli.fire_commands]
      mark=firemark.cli:mark
      """,
)
