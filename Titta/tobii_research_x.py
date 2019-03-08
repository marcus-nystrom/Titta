import tobiiresearch.implementation
from tobiiresearch.interop import interop
from importlib import import_module


# Import all modules defined in implementation/__init__.py
for module in tobiiresearch.implementation.__all__:
    import_module("tobiiresearch.implementation." + module)

# Make all globals in each module global in this module.
for module_name, module_content in tobiiresearch.implementation.__dict__.items():
    if module_name in tobiiresearch.implementation.__all__:
        for global_name, global_value in module_content.__dict__.items():
            if not global_name.endswith('__'):  # Don't import built in functionality.
                globals()[global_name] = global_value

__version__ = interop.get_sdk_version()

__copyright__ = '''
COPYRIGHT 2017 - PROPERTY OF TOBII AB
2017 TOBII AB - KARLSROVAGEN 2D, DANDERYD 182 53, SWEDEN - All Rights Reserved.

NOTICE:  All information contained herein is, and remains, the property of Tobii AB and its suppliers,
if any.  The intellectual and technical concepts contained herein are proprietary to Tobii AB and its suppliers and
may be covered by U.S.and Foreign Patents, patent applications, and are protected by trade secret or copyright law.
Dissemination of this information or reproduction of this material is strictly forbidden unless prior written
permission is obtained from Tobii AB.
'''

# Clean up so we don't export these internally used variables.
del module_name
del module_content
del global_name
del global_value
del module
del import_module
del tobiiresearch
del interop
