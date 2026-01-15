# su 

execv your with `setuid`

## build

`/usr/bin/clang -Os -fno-stack-protector suexec.c -o suexec`

`sudo chown root:wheel suexec && sudo chmod 4755 suexec`
