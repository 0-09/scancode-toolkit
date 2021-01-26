#
# Copyright (c) nexB Inc. and others. All rights reserved.
# SPDX-License-Identifier: Apache-2.0 AND CC-BY-4.0
#
# Visit https://aboutcode.org and https://github.com/nexB/scancode-toolkit for
# support and download. ScanCode is a trademark of nexB Inc.
#
# The ScanCode software is licensed under the Apache License version 2.0.
# The ScanCode open data is licensed under CC-BY-4.0.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import fnmatch
import logging
import sys


from commoncode import filetype
from commoncode.fileutils import file_name
from commoncode.fileutils import as_posixpath
from commoncode.fileutils import splitext_name
from packagedcode import PACKAGE_TYPES
from typecode import contenttype


TRACE = False

logger = logging.getLogger(__name__)


def logger_debug(*args):
    pass


if TRACE:
    logging.basicConfig(stream=sys.stdout)
    logger.setLevel(logging.DEBUG)

    def logger_debug(*args):
        return logger.debug(' '.join(isinstance(a, str)
                                     and a or repr(a) for a in args))

"""
Recognize package manifests in files.
"""


def recognize_packages(location):
    """
    Return a list of Package object if any packages were recognized for this
    `location`, or None if there were no Packages found. Raises Exceptions on errors.
    """

    if not filetype.is_file(location):
        return

    T = contenttype.get_type(location)
    ftype = T.filetype_file.lower()
    mtype = T.mimetype_file

    _base_name, extension = splitext_name(location, is_file=True)
    filename = file_name(location)
    extension = extension.lower()

    if TRACE:
        logger_debug('recognize_packages: ftype:', ftype, 'mtype:', mtype,
                     'pygtype:', T.filetype_pygment,
                     'fname:', filename, 'ext:', extension)

    recognized_packages = []
    for package_type in PACKAGE_TYPES:
        
        # 1. try as as a metafile
        if any(fnmatch.fnmatchcase(filename, metaf) for metaf in package_type.metafiles):
            for recognized in package_type.recognize(location):
                if TRACE:logger_debug('recognize_packages: metafile matching: recognized:', recognized)
                if recognized and not recognized.license_expression:
                    # compute and set a normalized license expression
                    recognized.license_expression = recognized.compute_normalized_license()
                    if TRACE:logger_debug('recognize_packages: recognized.license_expression:', recognized.license_expression)
                recognized_packages.append(recognized)
            return recognized_packages

        # 2. otherwise try type, mimetype and extension if matching
        type_matched = False
        if package_type.filetypes:
            type_matched = any(t in ftype for t in package_type.filetypes)

        mime_matched = False
        if package_type.mimetypes:
            mime_matched = any(m in mtype for m in package_type.mimetypes)

        extension_matched = False
        extensions = package_type.extensions
        if extensions:
            extensions = (e.lower() for e in extensions)
            extension_matched = any(fnmatch.fnmatchcase(extension, ext_pat)
                                    for ext_pat in extensions)

        if type_matched and mime_matched and extension_matched:
            if TRACE: logger_debug('recognize_packages: all matching')
            try:
                for recognized in package_type.recognize(location):
                    # compute and set a normalized license expression
                    if recognized and not recognized.license_expression:
                        recognized.license_expression = recognized.compute_normalized_license()
                    if TRACE: logger_debug('recognize_packages: recognized', recognized)
                    recognized_packages.append(recognized)
            except NotImplementedError:
                # build a plain package if recognize is not yet implemented
                recognized = package_type()
                if TRACE: logger_debug('recognize_packages: recognized', recognized)
                recognized_packages.append(recognized)
            return recognized_packages

        # 3. try as as an installed db
        posix_location = as_posixpath(location)
        if any(posix_location.endwith(idb) for idb in package_type.installed_dbs):
            for recognized in package_type.recognize(location):
                if TRACE:logger_debug('recognize_packages: metafile matching: recognized:', recognized)
                if recognized and not recognized.license_expression:
                    # compute and set a normalized license expression
                    recognized.license_expression = recognized.compute_normalized_license()
                    if TRACE:logger_debug('recognize_packages: recognized.license_expression:', recognized.license_expression)
                recognized_packages.append(recognized)
            return recognized_packages


        if TRACE: logger_debug('recognize_packages: no match for type:', package_type)
