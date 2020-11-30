PREFACE
=======

The goal of `clangTooling` is to be the easy way to satisfy dependencies on the `clangTooling` (and co) static libraries for building Python C/C++ extensions.
To support this, we will attempt to release wheels containing prebuilt binaries on all the platforms we can.


Mac/Linux
=========

These are the easy ones and are built via `cibuildwheel` in the CI.


Windows
=======

There are two flavors of Windows that we want to support: `win32` and `win_amd64`.
`cibuildwheel` seems to have trouble with this on the CI machines, but we can build the binaries locally and then upload to pypi manually.

I am using a bare-bones installation of Visual Studo 2019 to build everything with (I think the only extra thing I downloaded was the C++ stuff).
On x86 Windows 10, we need access to the the `Developer Command Prompt for VS 2019` and the `x86_x64 Cross Tools Command Prompt For VS 2019`.
We will be using the first to build native binaries and the latter to cross-compile for `win_amd64` wheels.

To build native binaries, open up the `Developer Command Prompt for VS 2019` -- all commands for `win32` will be done in this command prompt window.
We first call:

.. code-block::

   python build_windows.py -p win32

This will either create or update a local build of llvm/clang.  `setup.py` will install to a temporary directory, but we can save some time here by
making a local copy and doing incremental builds instead of a clean build every time.

After the cmake build is done, the source tree will have been populated with the headers and `.lib` binary files.  We can then run:

.. code-block::

   set CIBW_SKIP: cp27-* pp27-* cp35-* cp34-* cp33-*
   set CIBW_BUILD=*-win32
   cibuildwheel ./ --platform windows

This will produce wheels in a directory named `wheelhouse` which are ready to be uploaded to pypi.

To make the `win_amd64` wheels, open up the `x86_x64 Cross Tools Command Prompt For VS 2019`
-- all commands for `win_amd64` will be done in this command prompt window.  As before, run the build windows script:

.. code-block::

   python build_windows.py -p win_amd64

After the cmake build is done, we can then similarly run:

.. code-block::

   set CIBW_SKIP: cp27-* pp27-* cp35-* cp34-* cp33-*
   set CIBW_BUILD=*-win_amd64
   cibuildwheel ./ --platform windows

The wheels are again in the `wheelhouse` directory and are ready to be uploaded to pypi.
