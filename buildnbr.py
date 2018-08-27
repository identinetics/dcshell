#!/usr/bin/env python3

__author__ = 'r2h2'

import argparse
import difflib
import logging
import os
import re
import shutil
import sys

''' From the comparison between new and previous manifests compute a new build number 
    in case there was a change.
'''
def main(*cli_args):
    args = get_args(cli_args)
    logging.basicConfig()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    if args.subcommand == 'generate':
        manifest_lib = os.path.dirname(args.manifest_temp_name)
        (diff, last_manifest_name) = make_a_difference(args.manifest_temp_name, manifest_lib)
        if len('\n'.join(diff)) > 0:
            new_build_number = increment_build_number(last_manifest_name, args.manifest_scope)
            args.build_number_file.write(new_build_number)
            store_new_manifest(args.manifest_temp_name, new_build_number, manifest_lib, args.manifest_scope)
            write_log(diff, new_build_number, manifest_lib, args.manifest_scope)
            return new_build_number
        else:
            args.build_number_file.write(last_manifest_name)
    else:
        print(get_last_version('./manifest'))



def get_args(testargs=None):
    parser = argparse.ArgumentParser(
        description='Generate new build number or read the latest one for the docker image.',
        epilog='If there is a diff, then build# is incremented and the temp manifest is moved to '
               'manifest#buildno. Depending on MANIFEST_SCOPE in conf.sh the new '
               'manifest file is renamed and moved to ./manifest/global/ or ./manifest/local/'
        )
    subparsers = parser.add_subparsers(dest='subcommand', help='sub-command help')
    parser_create = subparsers.add_parser('generate')
    parser_create.add_argument('manifest_temp', type=argparse.FileType('r', encoding='utf8'),
                        help='Path of manifest of recent docker build. Must be in ./manifest/')
    parser_create.add_argument('manifest_scope', choices=['global', 'local'],
                        help='global or local (subdir in ./manifest/')
    parser_create.add_argument('build_number_file', type=argparse.FileType('w', encoding='utf8'),
                        help='resulting version number will be returned here')
    parser_create.add_argument('-d', '--debug', dest='debug', action="store_true")
    parser_read = subparsers.add_parser('read')
    parser_read.add_argument('-d', '--debug', dest='debug', action="store_true")
    if (testargs):
        args = parser.parse_args(testargs)
    else:
        args = parser.parse_args() # regular case: use sys.argv
    if args.subcommand == 'generate':
        args.manifest_temp_name = args.manifest_temp.name
        args.manifest_temp.close()
    return args


def make_a_difference(manifest_temp, manifest_lib) -> list:
    manifest_dirlist_global = []
    path = os.path.join(manifest_lib, 'global')
    os.makedirs(path, exist_ok=True)
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            manifest_dirlist_global.append(file)
    manifest_dirlist_local = []
    path = os.path.join(manifest_lib, 'local')
    os.makedirs(path, exist_ok=True)
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)) and not file.startswith('.'):
            manifest_dirlist_local.append(file)
    manifest_dirlist = sorted(manifest_dirlist_global + manifest_dirlist_local)
    if len(manifest_dirlist) > 0:
        _ = manifest_dirlist[-1:]
        last_manifest_name = _[0]
        if last_manifest_name in manifest_dirlist_global:
            last_manifest_path = os.path.join(manifest_lib, 'global', last_manifest_name)
        else:
            last_manifest_path = os.path.join(manifest_lib, 'local', last_manifest_name)
        with open(last_manifest_path) as fd:
            last_manifest = fd.readlines()
    else:
        last_manifest_name = '0.0'
        last_manifest = []
    with open(manifest_temp, encoding='utf-8') as fd:
        new_manifest = fd.readlines()
    _ = difflib.unified_diff(last_manifest, new_manifest)
    diff = '\n'.join(_)
    logging.debug("last_manifest_name: {}".format(last_manifest_name))
    #logging.debug(diff)
    return (diff, last_manifest_name)


def get_last_version(manifest_lib) -> str:
    manifest_dirlist_global = []
    path = os.path.join(manifest_lib, 'global')
    os.makedirs(path, exist_ok=True)
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)):
            manifest_dirlist_global.append(file)
    manifest_dirlist_local = []
    path = os.path.join(manifest_lib, 'local')
    os.makedirs(path, exist_ok=True)
    for file in os.listdir(path):
        if os.path.isfile(os.path.join(path, file)) and not file.startswith('.'):
            manifest_dirlist_local.append(file)
    manifest_dirlist = sorted(manifest_dirlist_global + manifest_dirlist_local,
                              key = lambda x: list(map(int, x.split('.'))))  # numeric sort on both parts of the string!
    if len(manifest_dirlist) > 0:
        _ = manifest_dirlist[-1:]
        last_manifest_name = _[0]
    else:
        last_manifest_name = ''
    return last_manifest_name


def increment_build_number(last_manifest_name, manifest_scope) -> str:
    m = re.match(r'(\d+)\.(\d+)$', last_manifest_name)
    if not m:
        raise Exception('Invalid manifest file name {}. '
                        'Must be S.T with S and T as integer'.format(last_manifest_name))
    else:
        source_buildno = int(m.group(1))
        target_buildno = int(m.group(2))
        if manifest_scope == 'global':
            source_buildno += 1
            target_buildno = 0
        else:
            target_buildno += 1
        buildno = "{}.{}".format(source_buildno, target_buildno)
        logging.info("Bumped version to {}".format(buildno))
        return buildno


def store_new_manifest(manifest_temp, new_build_number, manifest_lib, manifest_scope):
    new_path = os.path.join(manifest_lib, manifest_scope, new_build_number)
    os.makedirs(os.path.dirname(new_path), exist_ok=True)
    shutil.move(manifest_temp, new_path)
    logging.debug("moved from %s to %s" % (manifest_temp, new_path))


def write_log(diff, new_build_number, manifest_lib, manifest_scope):
    log_path = os.path.join(manifest_lib, manifest_scope, 'diff', new_build_number)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'w', encoding='utf-8') as fd:
        fd.write(diff)
    logging.debug("writing diff to %s" % log_path)


if __name__ == "__main__":
    main()
