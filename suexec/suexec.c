#include <unistd.h>
#include <stdio.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        char buf[1024];
        int len = snprintf(buf, sizeof(buf), "usage: %s <program> [args...]\n", argv[0]);
        write(2, buf, len);
        return 1;
    }

    // We're already running as root via setuid, so we can execute directly
    execv(argv[1], &argv[1]);

    // Only reached if exec fails
    perror("execv");
    return 1;
}

