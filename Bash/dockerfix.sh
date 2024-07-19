#!/bin/bash

# Reference links
# https://docs.docker.com/engine/install/debian/
# Possible error: Cannot connect to the Docker daemon at unix:///var/run/docker.sock. Is the docker daemon running?
# Solution link: https://shorturl.at/6fT5x

# Constant variable
Fixentry="[Unit]
Description=Docker Application Container Engine
Documentation=https://docs.docker.com
After=network-online.target docker.socket firewalld.service containerd.service time-set.target
Wants=network-online.target containerd.service
Requires=docker.socket

[Service]
Type=notify
# the default is not to use systemd for cgroups because the delegate issues still
# exists and systemd currently does not support the cgroup feature set required
# for containers run by docker
ExecStart=/usr/bin/dockerd -H fd:// -H unix:///var/run/docker.sock -H unix:///home/$USER/.docker/desktop/docker.sock --containerd=/run/containerd/containerd.sock
ExecReload=/bin/kill -s HUP $MAINPID
TimeoutStartSec=0
RestartSec=2
Restart=always

# Note that StartLimit* options were moved from "Service" to "Unit" in systemd 229.
# Both the old, and new location are accepted by systemd 229 and up, so using the old location
# to make them work for either version of systemd.
StartLimitBurst=3

# Note that StartLimitInterval was renamed to StartLimitIntervalSec in systemd 230.
# Both the old, and new name are accepted by systemd 230 and up, so using the old name to make
# this option work for either version of systemd.
StartLimitInterval=60s

# Having non-zero Limit*s causes performance problems due to accounting overhead
# in the kernel. We recommend using cgroups to do container-local accounting.
LimitNPROC=infinity
LimitCORE=infinity

# Comment TasksMax if your systemd version does not support it.
# Only systemd 226 and above support this option.
TasksMax=infinity

# set delegate yes so that systemd does not reset the cgroups of docker containers
Delegate=yes

# kill only the docker process, not all processes in the cgroup
KillMode=process
OOMScoreAdjust=-500

[Install]
WantedBy=multi-user.target"

# set user permissions
Set_User_permissions() {
    if groups $USER | grep -q docker; then
        echo "User is in docker group"
    else
        echo "User is not in docker group, adding user to docker group"
        sudo usermod -aG docker $USER
    fi

    echo "Setting docker to start on boot"
    # set docker to start on boot
    sudo systemctl enable docker
    sudo systemctl start docker

    # check if docker is running
    echo "Checking if docker is running"
    if sudo systemctl is-active --quiet docker; then
        echo Docker is running
    else
        echo Docker is not running
        sudo systemctl start docker
    fi

    # check if docker is enabled
    echo "Checking if docker is enabled"
    if sudo systemctl is-enabled --quiet docker; then
        echo Docker is enabled
    else
        echo Docker is not enabled
        sudo systemctl enable docker
    fi
}

docker_run_without_sudo() {
    # This will apply fixes to the docker service refer to line 4 "Possible error" by default
    echo "$Fixentry" | sudo tee /usr/lib/systemd/system/docker.service > /dev/null
    sudo systemctl daemon-reload
    sudo systemctl restart docker
    echo "Running Docker run hello-world"
    docker run hello-world
    exit 0
}

# check if the os is Ubuntu
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [ $ID = "ubuntu" ]; then
        echo "OS is Ubuntu"
        echo "Setting up Repositories"
        # Add Docker's official GPG key:
        sudo apt-get install ca-certificates curl -y
        sudo install -m 0755 -d /etc/apt/keyrings
        sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        sudo chmod a+r /etc/apt/keyrings/docker.asc

        # Add the repository to Apt sources:
        echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
        $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
        sudo apt-get update
        sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
        echo "Repositories set up"
        echo "Setting permissions"
        Set_User_permissions
        echo "Permissions set up"
        echo "Applying fixes to docker service"
        docker_run_without_sudo

    else
        echo "OS is not Ubuntu this script is for Ubuntu"
        sleep 5
        exit 1
    fi
else
    echo "OS is not Ubuntu"
    exit 1
fi
