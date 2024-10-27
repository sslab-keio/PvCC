#!/bin/bash
set -euxo pipefail

WORKDIR=`readlink -f $(dirname $0)`
IMGDIR="./images"
MNTDIR="./m-fstack"

mkdir ${MNTDIR}

dd if=/dev/zero of=${IMGDIR}/fstack.img bs=1G count=0 seek=16
mkfs.ext4 ${IMGDIR}/fstack.img
sudo mount ${IMGDIR}/fstack.img ${MNTDIR}
sudo cp -r --no-dereference --preserve ${IMGDIR}/debootstrap-jammy/* ${MNTDIR}/
sudo mkdir ${MNTDIR}/root/.ssh
sudo sh -c 'cat /root/.ssh/*.pub' | sudo tee ${MNTDIR}/root/.ssh/authorized_keys
sudo rsync --verbose -r ${IMGDIR}/debootstrap-jammy-diff/* ${MNTDIR}
cat ${IMGDIR}/hosts | grep "fstack-build" | while read mac ip host appip; do
    cat ./netplan/vm/01-external.yaml.template | sed "s/__IP__/${ip}\/24/" | sudo tee ${MNTDIR}/etc/netplan/01-external.yaml
done

sudo chroot ${MNTDIR} bash -ex << 'EOF'
locale-gen en_US.UTF-8
echo "root:r" | chpasswd
apt update
apt install -y git openssh-server libnuma-dev python3-pyelftools meson ninja-build build-essential libssl-dev gawk pkg-config libpcre3-dev zlib1g-dev autoconf gcc-12 pciutils
EOF

sudo umount ${MNTDIR}

sudo xl create ./domu-configs/fstack-build.cfg
until sudo ssh -o ConnectTimeout=1 root@192.168.70.200 : ; do sleep 1; done

sudo ssh root@192.168.70.200 bash -ex << 'EOF'
apt install -y linux-modules-`uname -r` linux-headers-`uname -r`
git clone https://github.com/F-Stack/f-stack.git /root/fstack
cd /root/fstack/dpdk
git checkout a4a53bacfcd7c3476c9c23b5a3003a99cb13d529
meson -Denable_kmods=true -Ddisable_libs=flow_classify build
ninja -C build
ninja -C build install

cd /root/fstack/lib
export FF_PATH=/root/fstack
export PKG_CONFIG_PATH=`which pkg-config`
make -j
make -j install

cd /root/fstack/app/nginx-1.25.2
bash ./configure --prefix=/usr/local/nginx_fstack --with-ff_module
make -j
make -j install

cd /root/fstack/app/redis-6.2.6/deps/jemalloc
./autogen.sh
cd /root/fstack/app/redis-6.2.6
make -j
make -j install
EOF

sudo xl destroy fstack-build


cat ${IMGDIR}/hosts | grep " fstack" | while read mac ip host appip; do
    sudo dd if=${IMGDIR}/fstack.img of=${IMGDIR}/${host}.img conv=sparse status=progress bs=1M
    sudo mount ${IMGDIR}/${host}.img ${MNTDIR}
    cat ./netplan/vm/01-external.yaml.template | sed "s/__IP__/${ip}\/24/" | sudo tee ${MNTDIR}/etc/netplan/01-external.yaml
    sudo sed -i -E "s/^addr=.*/addr=${appip}/g; s/^broadcast=.*/broadcast=10.0.0.255/g; s/^gateway=.*/gateway=10.0.0.1/g; s/^pkt_tx_delay=.*/pkt_tx_delay=0/g" ${MNTDIR}/usr/local/nginx_fstack/conf/f-stack.conf
    sudo sed -i "s/^bind.*/bind 127.0.0.1 -::1 ${appip}/" ${MNTDIR}/root/fstack/app/redis-6.2.6/redis.conf
    sudo umount ${MNTDIR}
done

rm -r ${MNTDIR}

