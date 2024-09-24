#!/bin/bash -ex

IMGDIR="./images"
MNTDIR="./m-sysbench"

mkdir $MNTDIR

dd if=/dev/zero of=${IMGDIR}/sysbench.img bs=1G count=0 seek=16
mkfs.ext4 ${IMGDIR}/sysbench.img
sudo mount ${IMGDIR}/sysbench.img ${MNTDIR}
sudo cp -r --no-dereference --preserve ${IMGDIR}/debootstrap-bionic/* ${MNTDIR}
sudo mkdir -p ${MNTDIR}/root/.ssh
sudo sh -c 'cat /root/.ssh/*.pub' | sudo tee ${MNTDIR}/root/.ssh/authorized_keys
sudo rsync --verbose -r ${IMGDIR}/debootstrap-bionic-diff/* $MNTDIR

sudo chroot ${MNTDIR} bash -ex << 'EOF'
locale-gen en_US.UTF-8
echo "root:r" | chpasswd
apt update
NEEDRESTART_MODE=a apt install -y openssh-server git sudo sysbench
EOF

sudo umount ${MNTDIR}

sudo dd if=${IMGDIR}/sysbench.img of=${IMGDIR}/loadvm1.img conv=sparse status=progress bs=1M
sudo mount ${IMGDIR}/loadvm1.img ${MNTDIR}
cat ./netplan/vm/01-external.yaml.template | sed "s/__IP__/192.168.70.101\/24/" | sudo tee ${MNTDIR}/etc/netplan/01-external.yaml
sudo umount ${MNTDIR}

rm -r ${MNTDIR}

