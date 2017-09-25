import setuptools
import re

with open('nutils_integration_matrix.py') as f:
  version = next(filter(None, map(re.compile("^__version__ = '([a-zA-Z0-9.]+)'$").match, f))).group(1)

setuptools.setup(
  name='nutils_integration_matrix',
  version=version,
  author='Evalf',
  py_modules=['nutils_integration_matrix'],
)

# vim: sts=2:sw=2:et
