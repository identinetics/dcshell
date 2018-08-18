#!/bin/bash

# This script must reside in the root of the docker project (same place as conf.sh)

main() {
    _get_commandline_opts $@
    _load_yaml_config
    _init_sudo
    _inspect_docker_build_env
    _inspect_container
}


_get_commandline_opts() {
    dc_config=docker-compose.y*ml
    while getopts ":f:" opt; do
      case $opt in
        f) dc_config=$OPTARG
        :) echo "Option -$OPTARG requires an argument"; exit 1;;
        *) echo "usage: $0 [-b] [-c] [-h] [-k] [-l] [-m] [-M] [-n <NN>] [-p] [-P] [-r] [-t tag] [-u] [cmd]
             -f  docker-compose config file
           "; exit 0;;
      esac
    done
    shift $((OPTIND-1))
}


_load_yaml_config() {
    SCRIPTDIR=$(cd $(dirname $BASH_SOURCE[0]) && pwd)
    PROJ_HOME=$(cd $(dirname $SCRIPTDIR) && pwd)
    config_script=$(echo $dc_config | sed -E 's/\.ya?ml$/.sh/')
    $SCRIPTDIR/config.sh -k 'CONTAINERNAME' -k 'IMAGENAME' $dc_config $PROJ_HOME/$config_script
    source $PROJ_HOME/$config_script
}


_init_sudo() {
    if (( $(id -u) != 0 )); then
        sudo='sudo -n' # ONLY used for `docker ..` commands
    fi
}


_echo_repo_version() {
    git remote -v | head -1 | \
        perl -ne 'm{(git\@github.com:|https://github.com/)(\S+) }; print "REPO::$2/"' | \
        perl -pe 's/\.git//'
    git symbolic-ref --short -q HEAD | tr -d '\n'
    printf '==#'
    git rev-parse --short HEAD
}


_inspect_git_repos() {
    find . -name '.git' | while read file; do
        repodir=$(dirname $file)
        cd $repodir
        _echo_repo_version
        cd $OLDPWD
    done
}


_inspect_from_image() {
    dockerfile_path="${DOCKERFILE_DIR}${DSCRIPTS_DOCKERFILE:-Dockerfile}"
    from_image_spec=$(egrep "^FROM" ${dockerfile_path} | awk '{ print $2}')
    if [[ "$from_image_spec" == *:* ]]; then
        image_id=$(${sudo} docker image ls --filter "reference=${from_image_spec}" -q | head -1)
    else  # if no tag is given, docker will assume :latest
        image_id=$(${sudo} docker image ls --filter "reference=${from_image_spec:latest}" -q | head -1)
    fi
    printf "FROM::${from_image_spec}==${image_id}\n"
}


_inspect_docker_build_env() {
    _inspect_git_repos
    _inspect_from_image
}


_inspect_container() {
    cmd="$sudo docker run -i --rm -u 0 --name=${CONTAINERNAME}_manifest ${IMAGENAME} /opt/bin/manifest2.sh"
}


main