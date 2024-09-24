#!/bin/bash
set -uxo pipefail

sudo pkill pvccsrv

sudo xl list | grep -v Domain-0 | grep -v Name | awk '{print $1}' | while read dom; do
        sudo xl destroy ${dom} &
done

while sudo xl list | grep -v Domain-0 | grep -v Name; do sleep 1; done

sudo xl cpupool-list | grep -v Name | grep -v Pool-0 | awk '{print $1}' | while read pool; do
	sudo xl cpupool-destroy ${pool}
done
for cpu in {0..23}; do
	sudo xl cpupool-cpu-add Pool-0 $cpu
done

