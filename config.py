#!/usr/bin/env python3

'''
Set the environment for shell scripts in dcshell:

$(config.py)

requires python3 in the path
'''

__author__ = 'r2h2'

import argparse
import collections
from collections import namedtuple
import filecmp
import io
import os
import pytest
import subprocess
import sys
import yaml

class CommandExecutionError(Exception):
    pass

def main(*cli_args):
    try:
        service_items = define_service_items()
        args = get_args(service_items, cli_args)
        (dc_config_dict, dc_service) = load_config_list(args.config_yaml_fd)
        key_value_list = map_service_items(dc_config_dict, dc_service, service_items, args.key)
        create_shell_script(key_value_list, dc_service, args.shellscript_fd)
    except CommandExecutionError as e:
        print(os.path.basename(__file__), 'failed.', str(e))
        sys.exit(1)

def define_service_items():
    # TODO: export DC_DOCKERFILE as path relative to DC_PROJ_HOME (if Dockerfile not in DC_PROJ_HOME
    return {
        'CONTAINERNAME': 'container_name',
        'CONTEXT': 'build.context',
        'DOCKERFILE': 'build.dockerfile',
        'ENVIRONMENT': 'environment',
        'HOSTNAME': 'hostname',
        'IMAGENAME': 'image',
    }

def get_args(service_items, testargs=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Read docker-compose-yaml file and write a bash scripts to stdout that will export '
                    'settings from a given list as shell variables. '
                    'Only the first service in docker-compose file is processed',
    )
    parser.add_argument('-D', '--projdir',
                        help='-D  specify project directory (file parameters will be relative to this path)')
    parser.add_argument('-f', '--config_yaml', action='append',
                        help='docker-compose config file (Default: docker-compose.ya?ml)')
    service_items_str = ' '.join(list(service_items.values()))
    parser.add_argument('-k', '--key', action='append',
                        help='select variable(s) (keys: {} )'.format(service_items_str))
    parser.add_argument('-s', '--shellscript', help='resulting shell script that can be sourced to '
                                             'export config values to the shell')
    if (testargs):
        args = parser.parse_args(testargs)
    else:
        args = parser.parse_args() # regular case: use sys.argv
    # open files for -f args
    if args.config_yaml is None:
        for f in ('docker-compose.yaml', 'docker-compose.yml'):
            if os.path.exists('{}/{}'.format(args.projdir, f)):
                args.config_yam = [f]
                break
    if args.config_yaml is None:
        raise CommandExecutionError('Default docker-compose.y*ml no found, and no -f option provided')
    args.config_yaml_fd = []
    for fpath_rel in args.config_yaml:
        fpath = fpath_rel if args.projdir is None else '{}/{}'.format(args.projdir, fpath_rel) # os.path.join broken
        try:
            args.config_yaml_fd.append(open(fpath, encoding='utf-8'))
        except Exception as e:
            raise CommandExecutionError('Cannot open -f', fpath)
    # open file for shell script arg
    if args.shellscript:
        try:
            fpath = args.shellscript if args.projdir is None else os.path.join(args.projdir,
                                                                               args.shellscript)
            args.shellscript_fd = open(fpath, 'w', encoding='utf-8')
        except Exception as e:
            raise CommandExecutionError('Cannot create', fpath)
    else:
        args.shellscript_fd = sys.stdout
    return args


def map_service_items(dc_config_dict, dc_service, service_items, filter_keys) -> dict:
    r = {}
    for key, dictitem in service_items.items():
        if dictitem.count('.') == 0:
            if filter_keys is None or dictitem in filter_keys:
                try:
                    r[key] = dc_config_dict['services'][dc_service][dictitem]
                except KeyError:
                    r[key] = ''
        elif dictitem.count('.') == 1:
            if filter_keys is None or dictitem in filter_keys:
                (k1, k2) = dictitem.split('.')
                try:
                    r[key] = dc_config_dict['services'][dc_service][k1][k2]
                except KeyError:
                    r[key] = ''
    return r


def load_config_list(config_yaml_list) -> list:
    dc_config_dict = load_config(config_yaml_list[0])
    for config_yaml in config_yaml_list[1:]:
        dict_merge(dc_config_dict, load_config(config_yaml))
    if 'version' not in dc_config_dict:
        raise CommandExecutionError('Docker-compose config version>=2 must contain "version:"')
    if not isinstance(dc_config_dict['services'], dict):
        raise CommandExecutionError('Docker-compose config: services must be a dict with exactly one service')
    dc_service = list(dc_config_dict['services'])[0]
    return (dc_config_dict, dc_service)


def load_config(config_yaml: io.TextIOBase) -> dict:
    try:
        cmd = 'envsubst <{}'.format(config_yaml.name)
        pipe = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout
        dc_config_dict = yaml.safe_load(pipe.read())
    except Exception as e:
        raise CommandExecutionError('Could not load {}: {}'.format(config_yaml.name, e))
    if not isinstance(dc_config_dict, dict):
        raise CommandExecutionError('Docker-compose config must be a dict at '
                                    'the top level. ({})'.format(config_yaml.name))
    return dc_config_dict


def create_shell_script(key_value_dict, dc_service, shell_script):
    shell_script.write("export DC_SERVICE={}\n".format(dc_service))
    for key, value in key_value_dict.items():
        if isinstance(value, dict):
            for k, v in value.items():
                shell_script.write("export {}_{}={}\n".format(value, k, v))
        elif isinstance(value, list):
            for i in value:
                equ = '' if '=' in i else '='
                shell_script.write("export {}_{}{}\n".format(key, i, equ))
        else:
            shell_script.write("export {}={}\n".format(key, value))


def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    """
    for k, v in merge_dct.items():
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]


# ---------- py.test ------------

def test_01_load_config():
    with open('test/testin/config/t01_dc.yaml', encoding='utf-8') as fd:
        expected_result = (
            {'version': '2',
             'services': {'shibsp': {'image': 'local/shibsp', 'container_name': 'shibsp'}}},
            'shibsp'
        )
        test_result = load_config_list([fd])
        assert  test_result == expected_result

def test_02_load_config_with_override():
    with open('test/testin/config/t02_dc.yaml', encoding='utf-8') as fd1:
        expected_result = (
            {'version': '2',
             'services': {'shibsp': {'image': 'r2h2/shibsp:pr', 'container_name': 'shibsp'}}},
            'shibsp'
        )
        with open('test/testin/config/t02_dc-override.yaml', encoding='utf-8') as fd2:
            test_result = load_config_list([fd1, fd2])
            assert  test_result == expected_result

def test_03_load_config_twoservices():
    expected_result = ({
        'version': '2',
        'services': {'shibsp': {'image': 'local/shibsp', 'container_name': 'shibsp'},
                     'shibsp2': {'image': 'local/shibsp2',
                                 'container_name': 'shibsp2'}}
         }, 'shibsp')
    with open('test/testin/config/t03_dc.yaml', encoding='utf-8') as fd:
        test_result = load_config_list([fd])
        assert test_result == expected_result


def test_04_load_broken_config():
    with open('test/testin/config/t04_dc_broken.yaml', encoding='utf-8') as fd:
        with pytest.raises(CommandExecutionError):
            assert load_config_list([fd])

def test_05_cli_default_keys():
    main('-f', 'test/testin/config/t05_dc.yaml', '-s', 'test/testout/t05_script.sh')
    assert(filecmp.cmp('test/testin/config/t05_script.sh', 'test/testout/t05_script.sh'))

def test_06_cli_singlekey():
    main('-k', 'container_name', '-f', 'test/testin/config/t06_dc.yaml', '-s', 'test/testout/t06_script.sh')
    assert(filecmp.cmp('test/testin/config/t06_script.sh', 'test/testout/t06_script.sh'))

def test_07_cli_twokeys():
    main('-k', 'container_name', '-k', 'image', '-f', 'test/testin/config/t07_dc.yaml', '-s', 'test/testout/t07_script.sh')
    assert(filecmp.cmp('test/testin/config/t07_script.sh', 'test/testout/t07_script.sh'))

def test_08_path_relative_to_prjdir():
    main('-k', 'container_name', '-D', 'test', '-f', '/testin/config/t08_dc.yaml', '-s', 'testout/t08_script.sh')
    assert(filecmp.cmp('test/testin/config/t08_script.sh', 'test/testout/t08_script.sh'))

def test_09_env_var_substitution():
    os.environ['TEST_IMAGENAME'] = 'testowner'
    main('-k', 'image', '-D', 'test', '-f', '/testin/config/t09_dc.yaml', '-s', 'testout/t09_script.sh')
    assert(filecmp.cmp('test/testin/config/t09_script.sh', 'test/testout/t09_script.sh'))

def test_10_with_nested_keys():
    main('-f', 'test/testin/config/t10_dc.yaml', '-s', 'test/testout/t10_script.sh')
    assert(filecmp.cmp('test/testin/config/t10_script.sh', 'test/testout/t10_script.sh'))



if __name__ == "__main__":
    main()
