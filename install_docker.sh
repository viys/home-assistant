#!/usr/bin/env bash
set -e

echo "==== Install Docker on Ubuntu ===="

# remove old versions
sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

# install dependencies
sudo apt update
sudo apt install -y ca-certificates curl gnupg

# add docker key
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
 | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

sudo chmod a+r /etc/apt/keyrings/docker.gpg

# add repo
echo \
"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo $VERSION_CODENAME) stable" \
| sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# install docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# enable docker
sudo systemctl enable docker
sudo systemctl start docker

# add user to docker group
sudo usermod -aG docker $USER

echo ""
echo "==== Docker Installed Successfully ===="
docker --version
echo ""
echo "Log out and log back in to use docker without sudo."