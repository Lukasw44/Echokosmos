import os
import sys
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

class get_pybind_include(object):
    def __init__(self, user=False):
        self.user = user

    def __str__(self):
        import pybind11
        return pybind11.get_include(self.user)

ext_modules = [
    Extension(
        'husarz',
        sources=['husarz.cpp'],
        include_dirs=[
            get_pybind_include(),
            get_pybind_include(user=True)
        ],
        language='c++'
    ),
]

class BuildExt(build_ext):
    def build_extensions(self):
        compiler_type = self.compiler.compiler_type
        opts = []
        link_opts = []

        if compiler_type == 'msvc':
            opts += [
                '/O2',
                '/Ox',
                '/Ot',
                '/Oi',
                '/openmp',
                '/std:c++17',
                '/arch:AVX2',
                '/GL',
                '/EHsc'
            ]
            link_opts += ['/LTCG']
        else:
            opts += ['-O3', '-fopenmp', '-std=c++17', '-march=native', '-ffast-math']
            link_opts += ['-fopenmp']

        for ext in self.extensions:
            ext.extra_compile_args = opts
            ext.extra_link_args = link_opts

        build_ext.build_extensions(self)

setup(
    name='husarz',
    version='1.0.4',
    author='System Labs',
    description='Echokosmos - Husarz v1.04',
    ext_modules=ext_modules,
    install_requires=['pybind11>=2.10.0', 'numpy'],
    cmdclass={'build_ext': BuildExt},
    zip_safe=False,
)
