"""
Custom build script for pypolychord.

This handles the complex build process that requires:
- Running make to build libchord.so from Fortran/C++ sources
- Compiling the C++ Python extension
- Handling MPI/non-MPI builds
"""

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext as _build_ext
from distutils.command.clean import clean as _clean

import os
import sys
import subprocess
import shutil

import numpy


def check_compiler(default_CC="gcc"):
    """Checks what compiler is being used (clang, intel, or gcc)."""
    CC = default_CC if "CC" not in os.environ else os.environ["CC"]
    try:
        CC_version = subprocess.check_output(
            [CC, "-v"], stderr=subprocess.STDOUT
        ).decode("utf-8").lower()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""

    if "clang" in CC_version:
        return "clang"
    elif "icc" in CC_version:
        return "intel"
    elif "gcc" in CC_version:
        return "gcc"
    else:
        print("Warning: unrecognised compiler: {}".format(CC_version))
        return ""


def get_compiler_flags():
    """Get compiler flags based on the detected compiler."""
    CC_FAMILY = check_compiler()
    CPPRUNTIMELIB_FLAG = []
    RPATH_FLAG = []

    if CC_FAMILY == "clang":
        CPPRUNTIMELIB_FLAG += ["-stdlib=libc++"]
        if sys.platform == "darwin":
            CPPRUNTIMELIB_FLAG += ["-mmacosx-version-min=10.9"]

    if sys.platform != "darwin":
        RPATH_FLAG += ["-Wl,-rpath,$ORIGIN/lib"]

    return CPPRUNTIMELIB_FLAG, RPATH_FLAG


class CustomBuildExt(_build_ext):
    """Custom build_ext that builds libchord.so before building the extension."""

    user_options = _build_ext.user_options + [
        ("no-mpi", None, "Don't compile with MPI support."),
        ("debug-flags", None, "Compile in debug mode."),
    ]

    def initialize_options(self):
        super().initialize_options()
        self.no_mpi = None
        self.debug_flags = None

    def finalize_options(self):
        super().finalize_options()

    def run(self):
        # Build libchord.so using make
        self._build_libchord()
        # Then build the Python extension
        super().run()

    def _build_libchord(self):
        """Run make to build libchord.so from Fortran/C++ sources."""
        BASE_PATH = os.path.dirname(os.path.abspath(__file__))

        env = dict(os.environ)
        env["CURDIR"] = BASE_PATH

        if self.no_mpi:
            env["MPI"] = "0"
        else:
            env["MPI"] = "1"
            # Get MPI compilers from makefile
            try:
                cc_compiler = subprocess.check_output(
                    ["make", "print_CC"], cwd=BASE_PATH
                ).decode('utf-8').strip()
                os.environ["CC"] = cc_compiler
                env["CC"] = cc_compiler

                cxx_compiler = subprocess.check_output(
                    ["make", "print_CXX"], cwd=BASE_PATH
                ).decode('utf-8').strip()
                os.environ["CXX"] = cxx_compiler
                env["CXX"] = cxx_compiler
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

        if self.debug_flags:
            env["DEBUG"] = "1"
            for ext in self.extensions:
                ext.extra_compile_args += ["-g", "-O0"]

        # Build libchord.so
        subprocess.check_call(["make", "-e", "libchord.so"], env=env, cwd=BASE_PATH)

        # Copy to pypolychord/lib/
        lib_dest = os.path.join(BASE_PATH, "pypolychord", "lib")
        os.makedirs(lib_dest, exist_ok=True)
        shutil.copy(
            os.path.join(BASE_PATH, "lib", "libchord.so"),
            lib_dest,
        )


class CustomClean(_clean):
    def run(self):
        try:
            subprocess.run(["make", "veryclean"], check=True, env=os.environ)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        return super().run()


# Get compiler flags
CPPRUNTIMELIB_FLAG, RPATH_FLAG = get_compiler_flags()

pypolychord_module = Extension(
    name="_pypolychord",
    library_dirs=["lib", "pypolychord/lib"],
    include_dirs=["src/polychord", numpy.get_include()],
    libraries=["chord"],
    extra_link_args=RPATH_FLAG + CPPRUNTIMELIB_FLAG,
    extra_compile_args=["-std=c++11"] + RPATH_FLAG + CPPRUNTIMELIB_FLAG,
    runtime_library_dirs=["lib", "pypolychord/lib"],
    sources=["pypolychord/_pypolychord.cpp"],
)

setup(
    ext_modules=[pypolychord_module],
    cmdclass={
        "build_ext": CustomBuildExt,
        "clean": CustomClean,
    },
)
