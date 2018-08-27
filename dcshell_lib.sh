#!/usr/bin/env bash

check_python3() {
    python3 -c exit >/dev/null 2>&1
    if (( $? > 0 )); then
        echo "python3 not found in path. Cannot proceed."
        exit 5
    fi
}


get_container_status() {
    if [[ "$($sudo docker ps -f name=$CONTAINERNAME |egrep -v ^CONTAINER)" ]]; then
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


