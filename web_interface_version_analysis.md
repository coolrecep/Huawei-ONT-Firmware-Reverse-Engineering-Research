# Web Interface Version Analysis Report
## Firmware Version: V500R021C00SPC128B125

### Executive Summary

**Can firmware version be obtained via web interface without root access?** 
**UNKNOWN** - The firmware version "V500R021C00SPC128B125" was found in NAND dumps, but accessibility via web interface without root access requires testing. The version is not directly exposed in the web interface filesystem without root access.

### Detailed Findings

#### 1. Firmware Version Location in NAND Dumps

**MTD Partitions Containing Version:**

- **mtd6_dump.bin (allsystemA)**: 4 occurrences of "V500R021C00SPC128B125"
- **mtd7_dump.bin (allsystemB)**: 4 occurrences of "V500R021C00SPC128B125"  
- **mtd11_dump.bin (file_system)**: 1 occurrence in backup filename "autobackup_V500R021C00SPC128B125"

**Partition Layout:**
```
mtd0: bootcode
mtd1: ubilayer_v5
mtd2: flash_configA
mtd3: flash_configB
mtd4: slave_paramA
mtd5: slave_paramB
mtd6: allsystemA (contains firmware version)
mtd7: allsystemB (contains firmware version)
mtd8: wifi_paramA
mtd9: wifi_paramB
mtd10: keyfile
mtd11: file_system (contains backup with version)
mtd12: app_system
```

#### 2. Version Information in Web Interface

**Finding:** The firmware version is stored in the web interface filesystem:

**File:** `/home/recep/Masaüstü/Firmware/squashfs-root-recovered/etc/version`
**Content:** `V500R021C00SPC128B125`

**Note:** This file is part of the squashfs-root-recovered directory which requires root access to dump the NAND flash. This is NOT accessible via HTTP without root access.

#### 3. Web Interface Endpoints

**Identified Web Interface Elements:**

**Servlet Endpoints:**
- `/diagnosis/servlet?cmd=getC`
- `/notice/servlet?cmd=getQ`
- `/notice/servlet?cmd=cancelAt`
- `/notice/getNotificationData`

**ASP Files Using Version Information:**
- Multiple ASP files use `InternetGatewayDevice.DeviceInfo` domain
- HardwareVersion and SoftwareVersion parameters are used in web interface

**Key ASP Files:**
- `/amp/awifi/server.asp` - Uses HardwareVersion parameter
- `/amp/wificoverinfo/wlancoverinfo.asp` - Uses HardwareVersion and SoftwareVersion
- `/amp/ontauth/password.asp` - Uses InternetGatewayDevice.DeviceInfo domain

#### 4. TR-069/CWMP Protocol

**Note:** TR-069/CWMP protocol works on fiber optics and requires specialized tools to access. This is not a viable method for obtaining firmware version via web interface without root access.

#### 5. Web Interface Access Without Root Access

**Accessibility Analysis:**

**UNKNOWN - Version accessibility without root access is uncertain because:**

1. **File Location:** The version file in `/etc/version` within the squashfs-root-recovered directory requires root access to dump the NAND flash. This is NOT directly accessible via HTTP without root access.

2. **TR-069 Protocol:** TR-069/CWMP protocol works on fiber optics and requires specialized tools to access. This is not a viable method for obtaining firmware version via web interface without root access.

3. **Web Interface Parameters:** The web interface ASP files use version parameters via `InternetGatewayDevice.DeviceInfo` domain, but these may require authentication to access.

4. **Potential Access Methods (Requires Testing):**
   - Login page may display version information
   - Status pages may show firmware version
   - Web interface API endpoints for device info (may require authentication)

#### 6. Specific Web Interface Access Points

**Potential Endpoints (Require Testing):**

Based on the analysis, the following endpoints may expose version information, but require authentication or testing to verify:

1. **Web Interface Status Pages:**
   - Login page may display version
   - Device information pages may be accessible without full authentication
   - Status pages often show firmware version

2. **API Endpoints:**
   - `/diagnosis/servlet?cmd=get*` endpoints
   - `/notice/servlet?cmd=get*` endpoints
   - Potential GET parameters for device information

#### 7. Testing Recommendations

**To verify web interface version access without root:**

1. **Check Login Page:**
   ```bash
   curl http://192.168.1.1/
   curl http://192.168.1.1/login.html
   ```

2. **Check Status Pages:**
   ```bash
   curl http://192.168.1.1/status.html
   curl http://192.168.1.1/deviceinfo.html
   ```

3. **Check API Endpoints:**
   ```bash
   curl http://192.168.1.1/api/deviceinfo
   curl http://192.168.1.1/api/status
   curl "http://192.168.1.1/diagnosis/servlet?cmd=getDeviceInfo"
   ```

#### 8. Conclusion

**Firmware version "V500R021C00SPC128B125" accessibility via web interface without root access is UNKNOWN and requires testing.**

**Evidence:**
1. Version file exists in web interface filesystem (`/etc/version`) but requires root access to dump NAND flash to access
2. TR-069/CWMP protocol is not a viable method as it requires specialized fiber optic tools
3. Web interface ASP files use version parameters via `InternetGatewayDevice.DeviceInfo` domain, but these may require authentication
4. Direct file access to `/etc/version` is not possible without root access
5. TR-069 XML structures require root access to NAND flash to access

**Potential Access Methods (Require Testing):**
1. Login page may display version information
2. Status pages may show firmware version
3. Web interface API endpoints for device info (may require authentication)

**Recommendation:** Test the suggested curl commands to verify if the firmware version is exposed via web interface endpoints without authentication. The version is confirmed to exist in the firmware, but accessibility without root access is not guaranteed.

---

**Analysis Date:** 2026-05-11
**Router Model:** Huawei HG8245X6
**Firmware Version:** V500R021C00SPC128B125
**Analysis Method:** NAND firmware dump analysis and web interface file extraction
