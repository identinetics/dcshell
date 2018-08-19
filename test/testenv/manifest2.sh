#!/bin/bash

# This script must be copied in the docker image to /opt/bin/manifest2.sh (-> Dockerfile)

main() {
    _get_system_python_packages                 #  requires pip
    #_get_venv_python_packages venv_path#       #  requires pip
    _get_singlefile_checksum /etc/passwd        #  requres sha256sum
    _get_directorytree_checksum /opt            #  requres sha256sum
}


_get_system_python_packages() {
    pip3 freeze | sed -e 's/^/PYTHON::/'
}


_get_venv_python_packages() {
    venv_path=$1
    source $venv_path/bin/activate
    venv=basename $venv_path
    pip3 freeze | sed -e "s/^/PYTHON\[${venv}\]::/"
}


_get_singlefile_checksum() {
    filepath=$1
    sha256sum $filepath | awk '{print "FILE::" $2 "==#" substr($1,1,7)}'
}


_get_directorytree_checksum() {
    path=$1
    find $path -type f -exec sha256sum {} + | awk '{print "FILE::" $2 "==#" substr($1,1,7)}'
}

main