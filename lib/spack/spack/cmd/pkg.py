# Copyright 2013-2019 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from __future__ import print_function

import os
import argparse

import llnl.util.tty as tty
from llnl.util.tty.colify import colify
from llnl.util.filesystem import working_dir

import spack.paths
import spack.repo
from spack.util.executable import which
from spack.cmd import spack_is_git_repo

description = "query packages associated with particular git revisions"
section = "developer"
level = "long"


def setup_parser(subparser):
    sp = subparser.add_subparsers(
        metavar='SUBCOMMAND', dest='pkg_command')

    add_parser = sp.add_parser('add', help=pkg_add.__doc__)
    add_parser.add_argument('packages', nargs=argparse.REMAINDER,
                            help="names of packages to add to git repo")

    list_parser = sp.add_parser('list', help=pkg_list.__doc__)
    list_parser.add_argument('rev', default='HEAD', nargs='?',
                             help="revision to list packages for")

    diff_parser = sp.add_parser('diff', help=pkg_diff.__doc__)
    diff_parser.add_argument(
        'rev1', nargs='?', default='HEAD^',
        help="revision to compare against")
    diff_parser.add_argument(
        'rev2', nargs='?', default='HEAD',
        help="revision to compare to rev1 (default is HEAD)")

    add_parser = sp.add_parser('added', help=pkg_added.__doc__)
    add_parser.add_argument(
        'rev1', nargs='?', default='HEAD^',
        help="revision to compare against")
    add_parser.add_argument(
        'rev2', nargs='?', default='HEAD',
        help="revision to compare to rev1 (default is HEAD)")

    add_parser = sp.add_parser('changed', help=pkg_changed.__doc__)
    add_parser.add_argument(
        'rev1', nargs='?', default='HEAD^',
        help="revision to compare against")
    add_parser.add_argument(
        'rev2', nargs='?', default='HEAD',
        help="revision to compare to rev1 (default is HEAD)")

    rm_parser = sp.add_parser('removed', help=pkg_removed.__doc__)
    rm_parser.add_argument(
        'rev1', nargs='?', default='HEAD^',
        help="revision to compare against")
    rm_parser.add_argument(
        'rev2', nargs='?', default='HEAD',
        help="revision to compare to rev1 (default is HEAD)")


def packages_path():
    """Get the test repo if it is active, otherwise the builtin repo."""
    try:
        return spack.repo.path.get_repo('builtin.mock').packages_path
    except spack.repo.UnknownNamespaceError:
        return spack.repo.path.get_repo('builtin').packages_path


def get_git():
    """Get a git executable that runs *within* the packages path."""
    git = which('git', required=True)
    git.add_default_arg('-C')
    git.add_default_arg(packages_path())
    return git


def list_packages(rev):
    pkgpath = packages_path()
    relpath = pkgpath[len(spack.paths.prefix + os.path.sep):] + os.path.sep

    git = get_git()
    with working_dir(spack.paths.prefix):
        output = git('ls-tree', '--full-tree', '--name-only', rev, relpath,
                     output=str)
    return sorted(line[len(relpath):] for line in output.split('\n') if line)


def pkg_add(args):
    """add a package to the git stage with `git add`"""
    pkgpath = packages_path()

    for pkg_name in args.packages:
        filename = spack.repo.path.filename_for_package_name(pkg_name)
        if not os.path.isfile(filename):
            tty.die("No such package: %s.  Path does not exist:" %
                    pkg_name, filename)

        git = get_git()
        with working_dir(spack.paths.prefix):
            git('-C', pkgpath, 'add', filename)


def pkg_list(args):
    """list packages associated with a particular spack git revision"""
    colify(list_packages(args.rev))


def diff_packages(rev1, rev2):
    p1 = set(list_packages(rev1))
    p2 = set(list_packages(rev2))
    return p1.difference(p2), p2.difference(p1)


def pkg_diff(args):
    """compare packages available in two different git revisions"""
    u1, u2 = diff_packages(args.rev1, args.rev2)

    if u1:
        print("%s:" % args.rev1)
        colify(sorted(u1), indent=4)
        if u1:
            print()

    if u2:
        print("%s:" % args.rev2)
        colify(sorted(u2), indent=4)


def pkg_removed(args):
    """show packages removed since a commit"""
    u1, u2 = diff_packages(args.rev1, args.rev2)
    if u1:
        colify(sorted(u1))


def pkg_added(args):
    """show packages added since a commit"""
    u1, u2 = diff_packages(args.rev1, args.rev2)
    if u2:
        colify(sorted(u2))


def pkg_changed(args):
    """show packages changed since a commit"""
    pkgpath = spack.repo.path.get_repo('builtin').packages_path
    rel_pkg_path = os.path.relpath(pkgpath, spack.paths.prefix)

    git = get_git()
    paths = git('diff', '--name-only', args.rev1, args.rev2, pkgpath,
                output=str).strip().split('\n')

    packages = set([])
    for path in paths:
        path = path.replace(rel_pkg_path + os.sep, '')
        pkg_name, _, _ = path.partition(os.sep)
        packages.add(pkg_name)

    colify(sorted(packages))


def pkg(parser, args):
    if not spack_is_git_repo():
        tty.die("This spack is not a git clone. Can't use 'spack pkg'")

    action = {'add': pkg_add,
              'diff': pkg_diff,
              'list': pkg_list,
              'removed': pkg_removed,
              'added': pkg_added,
              'changed': pkg_changed}
    action[args.pkg_command](args)
