#!/bin/bash
set -euxo pipefail

echo "GRUB_DISABLE_SUBMENU=y" | tee /etc/default/grub.d/mwae-disable-submenu
grub-reboot "Ubuntu GNU/Linux, with Xen 4.12.1-ae-pvcc and Linux `uname -r`"
reboot

