#!/usr/bin/env python3

__author__ = 'r2h2'

import argparse
from collections import namedtuple
import filecmp
import pytest
import yaml

class CommandExecutionError(Exception):
    pass

def main(*cli_args):
    service_items = define_service_items()
    args = get_args(service_items, cli_args)
    (dc_config_dict, dc_service) = load_config(args.config_yaml)
    key_value_list = map_service_items(dc_config_dict, dc_service, service_items, args.key)
    create_shell_script(key_value_list, args.shell_script)


def define_service_items():
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
        description='Read docker-compose-yaml file and create a bash scripts that will export '
                    'settings from a restricted list as shell variables. '
                    'Only 1 service per file is allowed',
    )
    parser.add_argument('config_yaml', type=argparse.FileType('r', encoding='utf8'),
                        help='docker-compose config file (YAML)')
    parser.add_argument('shell_script', type=argparse.FileType('w', encoding='utf8'),
                        help='resulting shell script that can be sourced to export config values to the shell')
    #parser.add_argument('-d', '--debug', dest='debug', action="store_true")
    service_items_str = ' '.join(list(service_items.values()))
    parser.add_argument('-k', '--key', action='append',
                        help='select variable(s) (keys: {} )'.format(service_items_str))
    if (testargs):
        args = parser.parse_args(testargs)
    else:
        args = parser.parse_args() # regular case: use sys.argv
    return args


def map_service_items(dc_config_dict, dc_service, service_items, filter_keys) -> dict:
    r = {}
    for key, dictitem in service_items.items():
        if dictitem.count('.') == 0:
            if filter_keys is None or key in filter_keys:
                try:
                    r[key] = dc_config_dict['services'][dc_service][dictitem]
                except KeyError:
                    r['# missing key: '] = key
        elif dictitem.count('.') == 1:
            if filter_keys is None or key in filter_keys:
                (k1, k2) = dictitem.split('.')
                try:
                    r[key] = dc_config_dict['services'][dc_service][k1][k2]
                except KeyError:
                    r['# missing key] = key
    return r



def load_config(config_yaml) -> list:
    try:
        dc_config_dict = yaml.safe_load(config_yaml)
    except Exception as e:
        raise CommandExecutionError('Could not load {}: {}'.format(config_yaml.name, e))
    if not isinstance(dc_config_dict, dict):
        raise CommandExecutionError('Docker-compose config must be a dict at the top level')
    if 'version' not in dc_config_dict:
        raise CommandExecutionError('Docker-compose config must container "version:"')
    if not isinstance(dc_config_dict['services'], dict) or (len(list(dc_config_dict['services'])) != 1):
        raise CommandExecutionError('Docker-compose config: services must be a dict with exactly one service')
    dc_service = list(dc_config_dict['services'])[0]
    return (dc_config_dict, dc_service)


def create_shell_script(key_value_dict, shell_script):
    for key, value in key_value_dict.items():
        if isinstance(value, dict):
            for k, v in value.items():
                shell_script.write("export {}_{}='{}'\n".format(value, k, v))
        elif isinstance(value, list):
            for i in value:
                equ = '' if '=' in i else '='
                shell_script.write("export {}_{}{}\n".format(key, i, equ))
        else:
            shell_script.write("export {}='{}'\n".format(key, value))

def test_load_config():
    expected_result1 = (
        {'version': '2', 'services': {'shibsp': {'image': 'local/shibsp', 'container_name': 'shibsp'}}},
        'shibsp'
    )
    with open('test/testin/docker-compose1.yaml', encoding='utf-8') as fd:
        test_result1 = load_config(fd)
        assert  test_result1 == expected_result1
    with open('test/testin/docker-compose2.yaml', encoding='utf-8') as fd:
        with pytest.raises(CommandExecutionError):
            assert load_config(fd)
    with open('test/testin/docker-compose4_broken.yaml', encoding='utf-8') as fd:
        with pytest.raises(CommandExecutionError):
            assert load_config(fd)

def test_main1():
    main('test/testin/docker-compose3.yaml', 'test/testout/script3.sh')
    assert(filecmp.cmp('test/testin/script3.sh', 'test/testout/script3.sh'))

def test_main2():
    main('-k', 'container_name', 'test/testin/docker-compose5.yaml', 'test/testout/script5a.sh')
    assert(filecmp.cmp('test/testin/script5a.sh', 'test/testout/script5a.sh'))

def test_main3():
    main('-k', 'container_name', '-k', 'image', 'test/testin/docker-compose5.yaml', 'test/testout/script5b.sh')
    assert(filecmp.cmp('test/testin/script5b.sh', 'test/testout/script5b.sh'))

if __name__ == "__main__":
    main()
