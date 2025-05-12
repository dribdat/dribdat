#!/bin/bash

# This is a deployment script for an Ubuntu VPS at Linode.com

# <UDF name="FQDN" Label="Fully qualified domain" example="dribdat.example.com" />
# <UDF name="TIME_ZONE" Label="Server time zone" example="Europe/Zurich" />

# Logs: tail -f /var/log/stackscript.log
# Logs: cat /var/log/stackscript.log
# Log to /var/log/stackscript.log for future troubleshooting

# Logging set up

exec 1> >(tee -a "/var/log/stackscript.log") 2>&1

function log {
  echo "### $1 -- `date '+%D %T'`"
}

# Common bash functions

source <ssinclude StackScriptID=1>

log "Common lib loaded"

# Apply harden script

source <ssinclude StackScriptID=394223>

# Update machine

log "Configuring System Updates"

apt-get -o Acquire::ForceIPv4=true update -y
DEBIAN_FRONTEND=noninteractive apt-get -y -o DPkg::options::="--force-confdef" -o DPkg::options::="--force-confold" install grub-pc
apt-get -o Acquire::ForceIPv4=true update -y

## Set hostname, configure apt and perform update/upgrade

log "Setting hostname"

IP=`hostname -I | awk '{print$1}'`
hostnamectl set-hostname $FQDN
echo $IP $FQDN  >> /etc/hosts

log "Updating .."

export DEBIAN_FRONTEND=noninteractive

apt-get update -y

## Remove older installations and get set for Docker install

log "Getting ready to install Docker"

sudo apt-get remove docker docker-engine docker.io containerd runc
sudo apt-get update
sudo apt-get install -y \
    apt-transport-https \
    ca-certificates \
    curl \
    make \
    gnupg-agent \
    software-properties-common \
    apache2-utils

log "Installing Docker Engine for $lsb_dist"

lsb_dist="$(. /etc/os-release && echo "$ID")"
lsb_dist="$(echo "$lsb_dist" | tr '[:upper:]' '[:lower:]')"

## Add Docker’s official GPG key

curl -fsSL "https://download.docker.com/linux/$lsb_dist/gpg" | sudo apt-key add -

## Install stable docker as daemon

add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/$lsb_dist \
   $(lsb_release -cs) \
   stable"

apt-get update
apt-get install -y docker-ce docker-ce-cli docker-compose containerd.io
systemctl enable docker

## Set up fail2ban

log "Installing fail2ban"

apt-get install fail2ban -y
cd /etc/fail2ban
cp fail2ban.conf fail2ban.local
cp jail.conf jail.local
systemctl start fail2ban
systemctl enable fail2ban

## Set up firewall with defaults ports

log "Configuring firewall"

apt-get install ufw -y
ufw default allow outgoing
ufw default deny incoming
ufw allow ssh
ufw allow https
ufw allow http
ufw enable
systemctl enable ufw
ufw logging off

## ----------------------------------------------

## Install & configure app

log "Installing dribdat"

mkdir -p /srv
cd /srv
cat <<END >.env
DRIBDAT_SECRET=`dd bs=32 count=1 if="/dev/urandom" | base64 | tr +/ _.`
DRIBDAT_APIKEY=`dd bs=16 count=1 if="/dev/urandom" | base64 | tr +/ _.`
SERVER_URL=$FQDN
END

# Commence installation

git clone https://github.com/dribdat/dribdat.git
mv .env dribdat
cd /srv/dribdat

log "Starting cloud deployment via docker-compose"

docker-compose --env-file .env -f docker-compose.yml up -d &

# Open http://$FQDN:1323/init to configure your server

log "After a minute, open: http://$FQDN:1323/init"

## ----------------------------------------------

echo "Installation complete!"
