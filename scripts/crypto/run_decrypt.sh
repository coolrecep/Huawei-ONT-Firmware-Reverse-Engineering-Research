#!/bin/bash
export QEMU_LD_PREFIX=/home/recep/Masaüstü/Firmware/arm-linux-musleabi-cross/arm-linux-musleabi
qemu-arm-static ./decrypt_tool "$1"
