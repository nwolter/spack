# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from spack import *


class Shoremap(MakefilePackage):
    """SHOREmap is a computational tool implementing a method that enables
       simple and straightforward mapping-by-sequencing analysis.

       Whole genome resequencing of pools of recombinant mutant genomes allows
       directly linking phenotypic traits to causal mutations. Such an
       analysis, called mapping-by-sequencing, combines classical genetic
       mapping and next generation sequencing by relying on selection-induced
       patterns within genome-wide allele frequency in pooled genomes."""

    homepage = "http://bioinfo.mpipz.mpg.de/shoremap/"
    url      = "http://bioinfo.mpipz.mpg.de/shoremap/SHOREmap_v3.6.tar.gz"

    version('3.6', 'ccc9331189705a139d50f2c161178cb1')

    depends_on('dislin')

    def edit(self, spec, prefix):
        makefile = FileFilter('makefile')
        makefile.filter(r'-L/usr/lib/',
                        self.spec['libxt'].libs.search_flags)
        makefile.filter(r'-L\./dislin.* -ldislin_d',
                        self.spec['dislin:d'].libs.ld_flags)

    def install(self, spec, prefix):
        mkdirp(prefix.bin)
        install('SHOREmap', prefix.bin)
