#!/bin/bash
set -euxo pipefail

WORKDIR=`readlink -f $(dirname $0)`
XENSRCDIR="${WORKDIR}/xen"
XENINSTDIR="${WORKDIR}/install"
XENVENDORVERSION="-ae-vanilla"
SYSTEMDINSTDIR="/usr/local/lib/systemd/system"

cd $XENSRCDIR
# ./configure --enable-systemd --prefix=${XENINSTDIR}
./configure --enable-systemd
make -j `nproc` dist || true
sed -i "s/git:\/\/git.qemu.org/https:\/\/gitlab.com\/qemu-project/; s/git:\/\/git.qemu-project.org/https:\/\/gitlab.com\/qemu-project/"  ${XENSRCDIR}/tools/qemu-xen-dir-remote/.gitmodules
rm ${XENSRCDIR}/tools/qemu-xen-dir-remote/.git/config
make -j `nproc` dist
sudo make -j `nproc` XEN_VENDORVERSION=$XENVENDORVERSION install
sudo ldconfig
sudo update-grub
# sudo mkdir -p ${SYSTEMDINSTDIR}
# sudo cp ${XENINSTDIR}/lib/systemd/system/* ${SYSTEMDINSTDIR}
sudo systemctl enable xen-qemu-dom0-disk-backend.service
sudo systemctl enable xen-init-dom0.service
sudo systemctl enable xenconsoled.service
sudo systemctl enable xendomains.service
sudo systemctl enable xen-watchdog.service
sudo systemctl enable xendriverdomain.service

