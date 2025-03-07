#!/pxrpythonsubst
#
# Copyright 2016 Pixar
#
# Licensed under the terms set forth in the LICENSE.txt file available at
# https://openusd.org/license.
#
from pxr import Tf
import sys

# Python 3 buffers output by default. We monkey-patch the print function here
# so that stdout is flushed after each print statement, thus producing the
# correct output. This doesn't work in python 2, even with the print function
# from __future__ because that version of the print function does not have a
# flush keyword parameter.
#
# On Windows with python 2 if this script is run with stdout redirected then
# the C++ stdout buffer is different from Python's stdout buffer.  As a result
# output from Python stdout and C++ stdout will not interleave as expected
# unless we flush both after each write.  We force flushing in Python here.
import platform
if sys.version_info.major >= 3:
    import functools
    print = functools.partial(print, flush=True)
elif platform.system() == 'Windows':
    import os
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'a+', 0)

sml = Tf.ScriptModuleLoader()

# Preload all currently known libraries to avoid their output in the test
# output.
sml._LoadModulesForLibrary('')

# Turn on script module loader debug output.
Tf.Debug.SetDebugSymbolsByName('TF_SCRIPT_MODULE_LOADER', True)

prefix = Tf.__package__ + '.testenv.testTfScriptModuleLoader_'

def Import(name):
    exec("import " + prefix + name)

# Declare libraries.
def Register(libs):
    for name, deps in libs:
        sml._RegisterLibrary(name, prefix + name, deps)

print ("# Test case: loading one library generates a request to load all\n"
       "# libraries, one of which attemps to import the library we're\n"
       "# currently loading.")
Register([
        ('LoadsAll', []),
        ('DepLoadsAll', ['LoadsAll']),
        ('Other', ['LoadsAll'])
        ])
print ("# This should attempt to (forwardly) load Other, which in turn tries\n"
       "# to import LoadsAll, which would fail, but we defer loading Other\n"
       "# until after LoadsAll is finished loading.")
sml._LoadModulesForLibrary('DepLoadsAll')

print ("# Registering a library that is totally independent, and raises an\n"
       "# error when loaded, but whose name comes first in dependency order.\n"
       "# Since there is no real dependency, the SML should not try to load\n"
       "# this module, which would cause an exception.")
Register([
        ('AAA_RaisesError', [])
        ])

print ("# Test case: loading one library dynamically imports a new,\n"
       "# previously unknown dependent library, which registers further\n"
       "# dependencies, and expects them to load.")
Register([
        ('LoadsUnknown', []),
        ('Test', ['LoadsUnknown'])
        # New dynamic dependencies discovered when loading LoadsUnknown.
        # ('Unknown', ['NewDynamicDependency']),
        # ('NewDynamicDependency', [])
        ])
print ("# This should load LoadsUnknown, which loads Unknown dynamically,\n"
       "# which should request for Unknown's dependencies (NewDependency) to\n"
       "# load, which should work.")
sml._LoadModulesForLibrary('Test')

