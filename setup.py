from distutils.core import setup
from Cython.Build import cythonize

setup(
  name = "Increment",
  ext_modules = cythonize("Increment.pyx"),
)