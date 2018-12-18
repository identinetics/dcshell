#!/bin/bash -e
PS4='+(${BASH_SOURCE}:${LINENO}): ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'

main() {
    # to be called from build, i.e. config already loaded
    _get_commandline_opts $@
    _load_dcshell_lib
    init_sudo
    _inspect_changes_in_docker_build_env
    _inspect_changes_in_container
}


_get_commandline_opts() {
    dc_config=docker-compose.y*ml
    f_opt_count=0
    while getopts ":f:v" opt; do
      case $opt in
        f) dc_config_opt="${dc_config_opt} -f ${OPTARG}";;
        v) verbose='True';;
        :) echo "Option -$OPTARG requires an argument"; exit 1;;
        *) echo "usage: $0 [-h] [-f file] [-v]
             -f  docker-compose config file
             -v  verbose
           "; exit 0;;
      esac
    done
    shift $((OPTIND-1))
    if (( f_opt_count > 1)); then
        echo "$0 does not support multiple compose files" && exit 1
    fi
}


_load_dcshell_lib() {
    source $DCSHELL_HOME/dcshell_lib.sh
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
    [[ $CONTEXT ]] && context_path="$CONTEXT/"
    dockerfile_path="${DC_PROJHOME}/${context_path}${DC_DOCKERFILE:-Dockerfile}"
    from_image_spec=$(egrep "^FROM" ${dockerfile_path} | awk '{ print $2}')
    if [[ "$from_image_spec" == *:* ]]; then
        image_id=$(${sudo} docker image ls --filter "reference=${from_image_spec}" -q | head -1)
    else  # if no tag is given, docker will assume :latest
        image_id=$(${sudo} docker image ls --filter "reference=${from_image_spec:latest}" -q | head -1)
    fi
    printf "FROM::${from_image_spec}==${image_id}\n"
}


_inspect_changes_in_docker_build_env() {
    _inspect_git_repos
    _inspect_from_image
}


_inspect_changes_in_container() {
    cmd="${sudo} docker-compose ${dc_config_opt} run --rm ${DC_SERVICE} /opt/bin/manifest2.sh"
    [[ "$verbose" ]] && echo $cmd
    $cmd
    rc=$?
}


main $@