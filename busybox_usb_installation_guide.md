#!/bin/bash

# Check Router Architecture Script
# Connect to router and determine CPU architecture

ROUTER_IP="192.168.1.1"

echo "=== Checking Router Architecture ==="

# Connect via Telnet and check architecture
{
    sleep 2
    echo "root"
    sleep 2
    echo "uname -m"
    sleep 2
    echo "cat /proc/cpuinfo | grep -E 'model name|processor'"
    sleep 2
    echo "exit"
} | timeout 15 telnet "$ROUTER_IP" 2>/dev/null

echo
echo "=== Architecture Detection Complete ==="
echo "Look for architecture in the output above:"
echo "- mips, mipsel, mips64, arm, arm64, i686, x86_64"
