# Copyright 2013-2020 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class Hcoll(Package):
    """Modern interface for Mellanox Fabric Collective Accelerator (FCA). FCA
    is a MPI-integrated software package that utilizes CORE-Direct technology
    for implementing the MPI collective communications."""

    homepage = 'https://www.mellanox.com/products/fca'
    has_code = False

    version('3.9.1927')

    # HCOLL needs to be added as an external package to SPACK. For this, the
    # config file packages.yaml needs to be adjusted:
    #
    # hcoll:
    #   version: [3.9.1927]
    #   paths:
    #     hcoll@3.9.1927: /opt/mellanox/hcoll (path to your HCOLL installation)
    #   buildable: False

    def install(self, spec, prefix):
        raise InstallError(
            self.spec.format('{name} is not installable, you need to specify '
                             'it as an external package in packages.yaml'))
