#!/usr/bin/env python3
"""
Huawei HG8245X6 Root Payload Generator
Based on the Turkish forum method for gaining root access
"""

import os
import shutil
import subprocess
import sys

def create_root_payload(version):
    """Create root payload for specified firmware version"""
    print("=" * 50)
    print(" HG8245X6 Universal Payload Generator ")
    print("=" * 50)
    print(f"Creating payload for version: {version}")
    
    build_dir = "payload_build"
    var_dir = os.path.join(build_dir, "var")
    
    # Clean old build directory
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(var_dir, exist_ok=True)
    
    # 1. Create signature file (main bash payload)
    signature_content = """#! /bin/sh
echo "=== HG8245X6 Custom Payload Execution ===" > /dev/console

# 1. Enable HW_SSMP_FEATURE_CLI_CHINA_MODE feature
echo 'feature.name = "HW_SSMP_FEATURE_CLI_CHINA_MODE" feature.enable="1" feature.attribute="1"' > /mnt/jffs2/hw_hardinfo_feature

# 2. Manipulate hw_ctree.xml file
var_jffs2_current_ctree_file="/mnt/jffs2/hw_ctree.xml"
var_current_ctree_bak_file="/var/hw_ctree_equipbak.xml"
var_current_ctree_file_tmp="/var/hw_ctree.xml.tmp"
var_node_telnet="InternetGatewayDevice.X_HW_Security.AclServices"
var_node_telnet_acs="InternetGatewayDevice.UserInterface.X_HW_CLITelnetAccess"

if [ -f "$var_jffs2_current_ctree_file" ]; then
    cp -f $var_jffs2_current_ctree_file $var_current_ctree_bak_file
    /bin/aescrypt2 1 $var_current_ctree_bak_file $var_current_ctree_file_tmp
    varIsXmlEncrypted=$?
    
    if [ $varIsXmlEncrypted -eq 0 ]; then
        mv $var_current_ctree_bak_file $var_current_ctree_bak_file".gz"
        gunzip -f $var_current_ctree_bak_file".gz"
    fi
    
    # Permanently enable Telnet
    cfgtool set $var_current_ctree_bak_file $var_node_telnet TELNETLanEnable 1
    cfgtool set $var_current_ctree_bak_file $var_node_telnet_acs Access 1
    
    # Close TR-069 ACS connection (for persistence)
    cfgtool set $var_current_ctree_bak_file "InternetGatewayDevice.ManagementServer" EnableCWMP 0
    
    if [ $varIsXmlEncrypted -eq 0 ]; then
        gzip -f $var_current_ctree_bak_file
        mv $var_current_ctree_bak_file".gz" $var_current_ctree_bak_file
        /bin/aescrypt2 0 $var_current_ctree_bak_file $var_current_ctree_file_tmp
    fi
    
    rm -f $var_jffs2_current_ctree_file
    cp -f $var_current_ctree_bak_file $var_jffs2_current_ctree_file
fi

# 3. Immediately start Telnet daemon
/sbin/telnetd -p 23 -l /bin/sh &
/sbin/telnetd -p 2323 -l /bin/sh &

echo "success!" > /dev/console
exit 0
"""
    
    signature_path = os.path.join(var_dir, "signature")
    with open(signature_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(signature_content)
    
    # Make executable (Unix executable structure)
    os.chmod(signature_path, 0o777)
    
    # 2. Create signinfo file (version information)
    with open(os.path.join(var_dir, "signinfo"), "w", encoding="utf-8", newline="\n") as f:
        f.write(version)
    
    # 3. Create item_list.txt file (map file)
    item_list_content = f"""0x504e5748 256 BB9|1029|997|734|393|323|627|767|1067|1007|AC7|10C7|147C|148C|14ED|15BD|120|130|140|141|150|160|170|171|180|190|1B1|1A1|1A0|1B0|1D0|1F1|201|211|221|230|240|260|261|270|271|280|281|291|2A1|431| + 0 file:/var/signature SIGNATURE {version} 2
+ 1 file:/var/signinfo SIGNINFO {version} 0
"""
    
    with open(os.path.join(build_dir, "item_list.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(item_list_content)
    
    print(f"\n[+] Required files created in '{build_dir}' directory.")
    print("[*] Running HuaweiFirmwareTool (hw_fmw)...\n")
    
    # 4. Run hw_fmw tool
    output_bin = f"HG8245X6_Payload_{version}.bin"
    
    try:
        # Use Popen to run hw_fmw
        # hw_fmw should be in system PATH or hw_fmw.exe should be in same directory
        result = subprocess.run(
            ["hw_fmw", "-d", ".", "-p", "-o", f"../{output_bin}"],
            cwd=build_dir,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"[SUCCESS] {output_bin} created successfully!")
            print("You can load this file to your device via ONT Enable Tool.")
            return True
        else:
            print("[ERROR] An error occurred while running hw_fmw tool.")
            print("Error Output:\n", result.stderr)
            print("\nPlease make sure 'hw_fmw' (HuaweiFirmwareTool) tool is installed on your computer and in PATH variable (or in this folder).")
            return False
            
    except FileNotFoundError:
        print("[ERROR] 'hw_fmw' command not found!")
        print("Please download the tool from https://github.com/0xuserpag3/HuaweiFirmwareTool")
        print("compile it and add 'hw_fmw.exe' to this directory or Windows PATH.")
        print(f"Then manually package the payload by running this command in '{build_dir}' folder:")
        print(f" hw_fmw -d . -p -o {output_bin}")
        return False

def main():
    """Main function"""
    print("=" * 50)
    print(" HG8245X6 Universal Payload Generator ")
    print("=" * 50)
    print("This tool creates root payload specific to the firmware version you specify.")
    
    version = input("Please enter the full version of the device (e.g: V500R021C00SPC128B125): ").strip()
    
    if not version:
        print("Error: Version number cannot be empty!")
        return
    
    success = create_root_payload(version)
    
    if success:
        print("\n[+] Root payload creation completed!")
        print("[*] Next steps:")
        print("    1. Load the generated .bin file via ONT Enable Tool")
        print("    2. Device will reboot with root access enabled")
        print("    3. Telnet will be available on ports 23 and 2323")
        print("    4. Connect via Telnet to get root shell")
    else:
        print("\n[-] Root payload creation failed!")
        print("[*] Please check hw_fmw tool installation and try again")

if __name__ == "__main__":
    main()
