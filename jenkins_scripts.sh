#!/bin/bash -exv
PS4='+(${BASH_SOURCE}:${LINENO}): ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'

# assure that python env has jinja2, pytest and pyyaml installed
source /usr/local/virtualenv/d.c/bin/activate

remove_containers() {
    echo 'remove containers'
    for cont in $*; do
        local container_found=$(docker container inspect -f '{{.Name}}' $cont 2>/dev/null || true)
        if [[ "$container_found" ]]; then
            docker container rm -f $container_found -v |  perl -pe 'chomp; print " removed\n"'
        fi
    done
}


