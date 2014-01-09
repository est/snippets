
SS Utility: Quick Intro

http://www.cyberciti.biz/files/ss.html

http://manpages.ubuntu.com/manpages/precise/en/man8/ss.8.html

http://lxr.free-electrons.com/source/net/ipv4/tcp_diag.c

http://lxr.free-electrons.com/source/include/uapi/linux/tcp.h#L90

/sbin/ss exclude TIME-WAIT -nt -a -oiem -p "sport == :http or sport == :https"

> http://superuser.com/a/173542/15252
> CLOSE_WAIT indicates that the other side of the connection has closed the connection. TIME_WAIT indicates that this side has closed the connection. The connection is being kept around so that any delayed packets can be matched to the connection and handled appropriately.