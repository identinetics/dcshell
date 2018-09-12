#!/bin/bash

# Replace docker registry owner 'local' by $DOCKER_REGISTRY_USER

perl -pe "s/^(\s+)image:\s+local/\$1image: $DOCKER_REGISTRY_USER/" $1
