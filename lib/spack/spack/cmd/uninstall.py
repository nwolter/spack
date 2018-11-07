# Copyright 2013-2018 Lawrence Livermore National Security, LLC and other
# Spack Project Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (Apache-2.0 OR MIT)

from __future__ import print_function

import argparse

import spack.cmd
import spack.environment as ev
import spack.package
import spack.cmd.common.arguments as arguments
import spack.repo
import spack.store

from llnl.util import tty
from llnl.util.tty.colify import colify

description = "remove installed packages"
section = "build"
level = "short"

error_message = """You can either:
    a) use a more specific spec, or
    b) use `spack uninstall --all` to uninstall ALL matching specs.
"""

# Arguments for display_specs when we find ambiguity
display_args = {
    'long': True,
    'show_flags': True,
    'variants': True,
    'indent': 4,
}


def add_common_arguments(subparser):
    subparser.add_argument(
        '-f', '--force', action='store_true', dest='force',
        help="remove regardless of whether other packages or environments "
        "depend on this one")
    arguments.add_common_arguments(
        subparser, ['recurse_dependents', 'yes_to_all'])


def setup_parser(subparser):
    add_common_arguments(subparser)
    subparser.add_argument(
        '-a', '--all', action='store_true', dest='all',
        help="USE CAREFULLY. Remove ALL installed packages that match each "
        "supplied spec. i.e., if you `uninstall --all libelf`,"
        " ALL versions of `libelf` are uninstalled. If no spec is "
        "supplied, all installed packages will be uninstalled. "
        "If used in an environment, all packages in the environment "
        "will be uninstalled.")

    subparser.add_argument(
        'packages',
        nargs=argparse.REMAINDER,
        help="specs of packages to uninstall")


def find_matching_specs(env, specs, allow_multiple_matches=False, force=False):
    """Returns a list of specs matching the not necessarily
       concretized specs given from cli

    Args:
        env (Environment): active environment, or ``None`` if there is not one
        specs (list): list of specs to be matched against installed packages
        allow_multiple_matches (bool): if True multiple matches are admitted

    Return:
        list of specs
    """
    # constrain uninstall resolution to current environment if one is active
    hashes = env.all_hashes() if env else None

    # List of specs that match expressions given via command line
    specs_from_cli = []
    has_errors = False
    for spec in specs:
        matching = spack.store.db.query(spec, hashes=hashes)
        # For each spec provided, make sure it refers to only one package.
        # Fail and ask user to be unambiguous if it doesn't
        if not allow_multiple_matches and len(matching) > 1:
            tty.error('{0} matches multiple packages:'.format(spec))
            print()
            spack.cmd.display_specs(matching, **display_args)
            print()
            has_errors = True

        # No installed package matches the query
        if len(matching) == 0 and spec is not any:
            if env:
                pkg_type = "packages in environment '%s'" % env.name
            else:
                pkg_type = 'installed packages'
            tty.die('{0} does not match any {1}.'.format(spec, pkg_type))

        specs_from_cli.extend(matching)

    if has_errors:
        tty.die(error_message)

    return specs_from_cli


def installed_dependents(specs):
    """Map each spec to a list of its installed dependents.

    Args:
        specs (list): list of Specs

    Returns:
        (dict): mapping from spec to lists of Environments

    """
    dependents = {}
    for item in specs:
        installed = spack.store.db.installed_relatives(
            item, 'parents', True)
        lst = [x for x in installed if x not in specs]
        if lst:
            lst = list(set(lst))
            dependents[item] = lst
    return dependents


def dependent_environments(specs):
    """Map each spec to environments that depend on it.

    This excludes the active environment, because we allow uninstalling
    from the active environment.

    Args:
        specs (list): list of Specs
    Returns:
        (dict): mapping from spec to lists of Environments

    """
    dependents = {}
    for env in ev.all_environments():
        if not env.active:
            hashes = set([s.dag_hash() for s in env.all_specs()])
            for spec in specs:
                if spec.dag_hash() in hashes:
                    dependents.setdefault(spec, []).append(env)
    return dependents


def do_uninstall(env, specs, force):
    """
    Uninstalls all the specs in a list.

    Args:
        env (Environment): active environment, or ``None`` if there is not one
        specs (list): list of specs to be uninstalled
        force (bool): force uninstallation (boolean)
    """
    packages = []
    for item in specs:
        try:
            # should work if package is known to spack
            packages.append(item.package)
        except spack.repo.UnknownEntityError:
            # The package.py file has gone away -- but still
            # want to uninstall.
            spack.package.Package.uninstall_by_spec(item, force=True)

        if env:
            try:
                # try removing the spec from the current active
                # environment. this will fail if the spec is not a root
                env.remove(item, force=True)
            except ev.SpackEnvironmentError:
                pass  # ignore non-root specs

    # Sort packages to be uninstalled by the number of installed dependents
    # This ensures we do things in the right order
    def num_installed_deps(pkg):
        dependents = spack.store.db.installed_relatives(
            pkg.spec, 'parents', True)
        return len(dependents)

    packages.sort(key=num_installed_deps)
    for item in packages:
        item.do_uninstall(force=force)

    # write any changes made to the active environment
    if env:
        env.write()


def get_uninstall_list(args, specs, env):
    # Gets the list of installed specs that match the ones give via cli
    # takes care of '-a' is given in the cli
    uninstall_list = find_matching_specs(env, specs, args.all, args.force)

    # Takes care of '-R'
    spec_dependents = installed_dependents(uninstall_list)
    spec_envs = dependent_environments(uninstall_list)

    # Process spec_dependents and update uninstall_list
    has_error = not args.force and (
        (spec_dependents and not args.dependents) or
        spec_envs)

    # say why each problem spec is needed
    if has_error:
        specs = set(list(spec_dependents.keys()) + list(spec_envs.keys()))
        for i, spec in enumerate(sorted(specs)):
            # space out blocks of reasons
            if i > 0:
                print()

            tty.info("Will not uninstall %s" % spec.cformat("$_$@$%@$/"),
                     format='*r')

            dependents = spec_dependents.get(spec)
            if dependents:
                print('The following packages depend on it:')
                spack.cmd.display_specs(dependents, **display_args)

            envs = spec_envs.get(spec)
            if envs:
                print('It is used by the following environments:')
                colify([e.name for e in envs], indent=4)

        msgs = []
        if spec_dependents:
            msgs.append(
                'use `spack uninstall --dependents` to uninstall dependents '
                'as well.')
        if spec_envs:
            msgs.append(
                'use `spack env remove` to remove environments, or '
                '`spack remove` to remove specs from environments.')
        if env:
            msgs.append('consider using `spack remove` to remove the spec '
                        'from this environment')
        print()
        tty.die('There are still dependents.', *msgs)

    elif args.dependents:
        for spec, lst in spec_dependents.items():
            uninstall_list.extend(lst)
        uninstall_list = list(set(uninstall_list))

    return uninstall_list


def uninstall_specs(args, specs):
    env = ev.get_env(args, 'uninstall', required=False)
    uninstall_list = get_uninstall_list(args, specs, env)

    if not uninstall_list:
        tty.warn('There are no package to uninstall.')
        return

    if not args.yes_to_all:
        tty.msg('The following packages will be uninstalled:\n')
        spack.cmd.display_specs(uninstall_list, **display_args)
        answer = tty.get_yes_or_no('Do you want to proceed?', default=False)
        if not answer:
            tty.die('Will not uninstall any packages.')

    # Uninstall everything on the list
    do_uninstall(env, uninstall_list, args.force)


def uninstall(parser, args):
    if not args.packages and not args.all:
        tty.die('uninstall requires at least one package argument.',
                '  Use `spack uninstall --all` to uninstall ALL packages.')

    # [any] here handles the --all case by forcing all specs to be returned
    uninstall_specs(
        args, spack.cmd.parse_specs(args.packages) if args.packages else [any])
