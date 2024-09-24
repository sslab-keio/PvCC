#!/bin/bash -ex

WORKDIR=`readlink -f $(dirname $0)`
IMGDIR="./images"
MNTDIR="./m-seastar"

mkdir ${MNTDIR}

dd if=/dev/zero of=${IMGDIR}/seastar.img bs=1G count=0 seek=16
mkfs.ext4 ${IMGDIR}/seastar.img
sudo mount ${IMGDIR}/seastar.img ${MNTDIR}
sudo cp -r --no-dereference --preserve ${IMGDIR}/debootstrap-bionic/* ${MNTDIR}/
sudo mkdir -p ${MNTDIR}/root/.ssh
sudo sh -c 'cat /root/.ssh/*.pub' | sudo tee ${MNTDIR}/root/.ssh/authorized_keys
sudo rsync --verbose -r ${IMGDIR}/debootstrap-bionic-diff/* ${MNTDIR}

sudo chroot ${MNTDIR} bash -ex << 'EOF'
locale-gen en_US.UTF-8
echo "root:r" | chpasswd
apt update
NEEDRESTART_MODE=a apt install -y openssh-server git pciutils cmake linux-modules-4.15.0-213-generic sudo
git clone https://github.com/scylladb/seastar.git /root/seastar

cd /root/seastar
git checkout seastar-18.08-branch
git submodule update --init --recursive
sed -i "s/IXGBE_DEFAULT_TX_RSBIT_THRESH 32/IXGBE_DEFAULT_TX_RSBIT_THRESH 1/" dpdk/drivers/net/ixgbe/ixgbe_ethdev.c
./install-dependencies.sh 
./configure.py --mode=release --enable-dpdk
ninja
EOF

sudo umount ${MNTDIR}

cat ${WORKDIR}/hosts | grep seastar | while read mac ip host appip; do
    sudo dd if=${IMGDIR}/seastar.img of=${IMGDIR}/${host}.img conv=sparse status=progress bs=1M
    sudo mount ${IMGDIR}/${host}.img ${MNTDIR}
    cat ./netplan/vm/01-external.yaml.template | sed "s/__IP__/${ip}\/24/" | sudo tee ${MNTDIR}/etc/netplan/01-external.yaml
    sudo umount ${MNTDIR}
done

rm -r ${MNTDIR}

