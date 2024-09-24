#!/bin/bash
set -euxo pipefail

WORKDIR=`readlink -f $(dirname $0)`
XENSRCDIR="${WORKDIR}/xen-source"
XENINSTDIR="${WORKDIR}/install"
PATCH="${WORKDIR}/pvcc.patch"
XENVENDORVERSION="-ae-pvcc"

cd $XENSRCDIR
git apply $PATCH
./configure --enable-systemd --prefix=${XENINSTDIR}
make -j `nproc` dist || true
sed -i "s/git:\/\/git.qemu.org/https:\/\/gitlab.com\/qemu-project/; s/git:\/\/git.qemu-project.org/https:\/\/gitlab.com\/qemu-project/" ${XENSRCDIR}/tools/qemu-xen-dir-remote/.gitmodules
rm ${XENSRCDIR}/tools/qemu-xen-dir-remote/.git/config
make -j `nproc` dist
sudo make -j `nproc` XEN_VENDORVERSION=$XENVENDORVERSION install

