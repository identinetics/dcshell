#!/bin/bash

# assuming an tar archive has been created from /var/lib/docker/volumes/<volname>, then
# extracted into /tmp at the target system, and
# assuming that the docker-compose.yaml file has been moved to the well-known location /di/<projname>,
# this script can:
#    - create volumes by running the container (dc??.yaml is in current directory)
#    - restore contents of docker volumes
#    - copy volumes to a remote host
#    - init volumes on remote host and create directories

# Whan extracting tar archives, make sure to restore
function execcmd() {
    cmd=$1
    echo $cmd
    $cmd
}

function create_container() {
    imgid=$1
    service=$2
    execcmd "docker-compose -f dc${imgid}.yaml run --rm ${service}${imgid} echo bye"
}

function copy_vol() {
    cmd="cp -pr /tmp/$OLD_CONTAINER.$1/* /var/lib/docker/volumes/$NEW_CONTAINER.$1/"
    echo $cmd
    $cmd
    dlink.sh $NEW_CONTAINER.$1 /dv
}

function rsync_vol() {
    volname=$1
    execcmd "ssh ${TARGET_HOST} docker volume create $NEW_CONTAINER.${volname}"
    execcmd "rsync --archive --progress --stats --compress --rsh=/usr/bin/ssh --recursive --relative --times --perms --links /var/lib/docker/volumes/$OLD_CONTAINER.${volname}/_data/* ${TARGET_HOST}:/var/lib/docker/volumes/$NEW_CONTAINER.${volname}/_data/"
}

function mkvol_shibidp() {
    ssh ${TARGET_HOST} docker volume create $NEW_CONTAINER.$1  
}

function mklogvol() {
    ssh ${TARGET_HOST} docker volume create $NEW_CONTAINER.var_log  
    ssh ${TARGET_HOST} mkdir -p /var/lib/docker/volumes/$NEW_CONTAINER.var_log/_data/$1
    ssh ${TARGET_HOST} chown $2 /var/lib/docker/volumes/$NEW_CONTAINER.var_log/_data/$1
}

function mklogvol_shibidp() {
    ssh ${TARGET_HOST} docker volume create $NEW_CONTAINER.var_log  
    ssh ${TARGET_HOST} mkdir -p /var/lib/docker/volumes/$NEW_CONTAINER.var_log/_data/jetty \
             /var/lib/docker/volumes/$NEW_CONTAINER.var_log/_data/idp
    ssh ${TARGET_HOST} chown 343007 /var/lib/docker/volumes/$NEW_CONTAINER.var_log/_data/jetty \
                /var/lib/docker/volumes/$NEW_CONTAINER.var_log/_data/idp
}

function scp_shibidp() {
    rsync_vol etc_pki_shib-idp
    rsync_vol opt_jetty-base
    rsync_vol opt_shibboleth-idp
    mklogvol_shibidp
}


function copy_shibidp() {
    copy_vol etc_pki_shib-idp
    copy_vol opt_jetty-base
    copy_vol opt_shibboleth-idp
    mkdir -p /var/lib/docker/volumes/$NEW_CONTAINER.var_log/jetty \
             /var/lib/docker/volumes/$NEW_CONTAINER.var_log/idp
    chown 343007 /var/lib/docker/volumes/$NEW_CONTAINER.var_log/_data/jetty \
                /var/lib/docker/volumes/$NEW_CONTAINER.var_log/_data/idp
}

function copy_shibsp() {
    copy_vol etc_httpd_conf
    copy_vol etc_httpd_conf.d
    copy_vol etc_shibboleth
    copy_vol opt_etc
    copy_vol var_www
}

function copy_openldap() {
    copy_vol db
    copy_vol etc
    copy_vol log
}

# nginx from nc8 to nc9

TARGET_HOST=nc9
OLD_CONTAINER=dnginx_02nginx
NEW_CONTAINER=test_02nginx
rsync_vol etc_letsencrypt

# samlschematron from nc8 to nc9

TARGET_HOST=nc9
OLD_CONTAINER=04samlschtron
NEW_CONTAINER=04samlschtron
copy_vol etc_pki
mklogvol dummy

# === Shibboleth IDPs from nc9 to nc1 ===
TARGET_HOST=nc1
OLD_CONTAINER=dc_19shibidp
NEW_CONTAINER=19shibidp
copy_vol scp_shibidp

# === openldap from nc8 ===
OLD_CONTAINER=06openldap
NEW_CONTAINER=dc_06openldap
docker-compose run --rm openldap echo bye
copy_openldap


# === Shibboleth IDPs from nc8 ===
OLD_CONTAINER=dc_07shibidp
NEW_CONTAINER=dc_07shibidp
create_container '07' 'shibidp'
copy_shibidp

OLD_CONTAINER=dc_shibidp14
NEW_CONTAINER=dc_14shibidp
create_container '14' 'shibidp'
copy_shibidp

OLD_CONTAINER=dc_shibidp19
NEW_CONTAINER=dc_19shibidp
create_container '19' 'shibidp'
copy_shibidp

# === Shibboleth SPs from nc8 (only volumes) ===
OLD_CONTAINER=dshibsp_05sp1testwpv
NEW_CONTAINER=dc_05shibsp
copy_shibsp
OLD_CONTAINER=dshibsp_08
NEW_CONTAINER=dc_08shibsp
copy_shibsp
OLD_CONTAINER=dshibsp_13sp3testwpv
NEW_CONTAINER=dc_13shibsp
copy_shibsp
OLD_CONTAINER=dshibsp_20echopvgvat
NEW_CONTAINER=dc_20shibsp
copy_shibsp
OLD_CONTAINER=dshibsp_21sp2testpvgvat
NEW_CONTAINER=dc_21shibsp
copy_shibsp
OLD_CONTAINER=dshibsp_45sp1testpvgvat
NEW_CONTAINER=dc_45shibsp
copy_shibsp
OLD_CONTAINER=dshibsp_47testspwpvpvat
NEW_CONTAINER=dc_47shibsp
copy_shibsp
OLD_CONTAINER=dshibsp_49mdregtestpvgvat
NEW_CONTAINER=dc_49shibsp
copy_shibsp