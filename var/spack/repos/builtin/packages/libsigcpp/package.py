##############################################################################
# Copyright (c) 2013-2018, Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory.
#
# This file is part of Spack.
# Created by Todd Gamblin, tgamblin@llnl.gov, All rights reserved.
# LLNL-CODE-647188
#
# For details, see https://github.com/spack/spack
# Please also see the NOTICE and LICENSE files for our notice and the LGPL.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License (as
# published by the Free Software Foundation) version 2.1, February 1999.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the IMPLIED WARRANTY OF
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the terms and
# conditions of the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
##############################################################################
from spack import *


class Libsigcpp(AutotoolsPackage):
    """Libsigc++ is a C++ library for typesafe callbacks"""

    homepage = "https://libsigcplusplus.github.io/libsigcplusplus/index.html"
    url      = "https://ftp.acc.umu.se/pub/GNOME/sources/libsigc++/2.0/libsigc++-2.0.3.tar.gz"

    version('2.9.3', '0e5630fd0557ee80b5e5cbbcebaa2594')
    version('2.1.1', '5ae4d6da9a408c90e86c776673c38972')
    version('2.0.3', '57c6887dd46ce0bd312a4823589db5d8')

    def url_for_version(self, version):
        """Handle version-based custom URLs."""
        url = "https://ftp.acc.umu.se/pub/GNOME/sources/libsigc++"
        ext = '.tar.gz' if version < Version('2.2.10') else '.tar.xz'
        return url + "/%s/libsigc++-%s%s" % (version.up_to(2), version, ext)
