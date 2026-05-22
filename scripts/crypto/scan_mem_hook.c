#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

void __attribute__((constructor)) init() {
    FILE *log = fopen("/tmp/mem_scan.log", "w");
    if (!log) return;
    
    fprintf(log, "Scanning memory for ALPHA table...\n");
    
    // We will scan the memory of the current process.
    // To do this safely, we read /proc/self/maps to find readable regions.
    FILE *maps = fopen("/proc/self/maps", "r");
    if (!maps) {
        fclose(log);
        return;
    }
    
    char line[256];
    while (fgets(line, sizeof(line), maps)) {
        unsigned long start, end;
        char perms[5];
        if (sscanf(line, "%lx-%lx %4s", &start, &end, perms) == 3) {
            // Only scan readable regions
            if (perms[0] == 'r') {
                fprintf(log, "Scanning region %lx-%lx %s\n", start, end, perms);
                
                unsigned char *p = (unsigned char *)start;
                unsigned long size = end - start;
                
                for (unsigned long i = 0; i < size - 32; i++) {
                    unsigned char *b = p + i;
                    // Check our constraints
                    if (b[1] == 57 && b[2] == 72 && b[3] == 82 && b[4] == 69 &&
                        b[7] == 57 && b[10] == 33 && b[11] == 80 && b[15] == 52 &&
                        b[18] == 72 && b[19] == 69 && b[22] == 76 && b[30] == 57) {
                        
                        fprintf(log, "MATCH FOUND AT %lx!\n", (unsigned long)b);
                        fprintf(log, "Table: ");
                        for(int j=0; j<32; j++) {
                            fprintf(log, "%02x ", b[j]);
                        }
                        fprintf(log, "\nASCII: ");
                        for(int j=0; j<32; j++) {
                            fprintf(log, "%c", (b[j] >= 32 && b[j] <= 126) ? b[j] : '.');
                        }
                        fprintf(log, "\n");
                    }
                }
            }
        }
    }
    fclose(maps);
    fprintf(log, "Scan complete.\n");
    fclose(log);
}
