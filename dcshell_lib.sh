#!/usr/bin/env bash
PS4='+(${BASH_SOURCE}:${LINENO}): ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'

check_python3() {
    python3 -c exit >/dev/null 2>&1
    if (( $? > 0 )); then
        echo "python3 not found in path. Cannot proceed."
        exit 5
    fi
}


get_container_status() {
    if [[ ! "$CONTAINERNAME" ]]; then
        echo 'CONTAINERNAME must not be empty'
        exit 1
    elif [[ "$($sudo docker ps -f name=$CONTAINERNAME |egrep -v ^CONTAINER)" ]]; then
        return 0   # running
    elif [[ "$($sudo docker ps -a -f name=$CONTAINERNAME|egrep -v ^CONTAINER)" ]]; then
        return 1   # stopped
    else
        return 2   # not found
    fi
}


init_sudo() {
    # set sudo unless there is write access to the docker socket (ignoring the TCP use case)
    if [[ ! -w "/var/run/docker.sock" ]]; then
        sudo='sudo -n -E'  # preserve the env, to pass vars from jenkins to compose.yaml
    fi
}


load_compose_yaml_config() {
    set -e
    check_python3
    # config.py will create 'export X=Y' statements on stdout; source it by executing the subshell
    tmpfile="/tmp/dcshell-build${$}"
    $($DCSHELL_HOME/config.py $projdir_opt \
        -k container_name -k image -k build.context -k build.dockerfile $dc_opt_prefixed) \
        > $tmpfile
    source $tmpfile
    set +e
    rm -f $$tmpfile
}


