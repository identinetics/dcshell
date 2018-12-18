#!/bin/bash -e

# Replace docker registry owner 'local' by $DOCKER_REGISTRY_USER

if [[ -e "$1" ]]; then
    perl -pe "s/^(\s+)image:\s+local/\$1image: $DOCKER_REGISTRY_USER/" $1 > $2
fi
