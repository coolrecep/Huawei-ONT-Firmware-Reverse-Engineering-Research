#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

int main(int argc, char **argv) {
    printf("Running aescrypt2 directly using execve...\n");
    char *args[] = {"/bin/aescrypt2", "1", "/tmp/hw_ctree.xml", "/tmp/hw_ctree.decrypted.xml", NULL};
    execve(args[0], args, NULL);
    perror("execve failed");
    return 0;
}
