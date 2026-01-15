#include <unistd.h>
#include <stdio.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        write(2, "usage: execwrap <program> [args...]\n", 37);
        return 1;
    }

    execv(argv[1], &argv[1]);

    // Only reached if exec fails
    perror("execv");
    return 1;
}

