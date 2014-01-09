import re, socket, struct


"""

# http://lxr.free-electrons.com/source/net/ipv4/tcp_diag.c



typedef struct
{
	__u8 family;
	__u8 bytelen;
	__s16 bitlen;
	__u32 flags;
	__u32 data[8];
} inet_prefix;

struct tcpstat
{
	inet_prefix	local;
	inet_prefix	remote;
	int		lport;
	int		rport;
	int		state;
	int		rq, wq;
	int		timer;
	int		timeout;
	int		retrs;
	unsigned	ino;
	int		probes;
	unsigned	uid;
	int		refcnt;
	unsigned long long sk;
	int		rto, ato, qack, cwnd, ssthresh;
};

/* Socket identity */
struct inet_diag_sockid {
	__be16	idiag_sport;
	__be16	idiag_dport;
	__be32	idiag_src[4];
	__be32	idiag_dst[4];
	__u32	idiag_if;
	__u32	idiag_cookie[2];
#define INET_DIAG_NOCOOKIE (~0U)
};

/* Request structure */

struct inet_diag_req {
	__u8	idiag_family;		/* Family of addresses. */
	__u8	idiag_src_len;
	__u8	idiag_dst_len;
	__u8	idiag_ext;		/* Query extended information */

	struct inet_diag_sockid id;

	__u32	idiag_states;		/* States to dump */
	__u32	idiag_dbs;		/* Tables to dump (NI) */
};

struct inet_diag_req_v2 {
	__u8	sdiag_family;
	__u8	sdiag_protocol;
	__u8	idiag_ext;
	__u8	pad;
	__u32	idiag_states;
	struct inet_diag_sockid id;
};

struct nlmsghdr
{
  __u32 nlmsg_len;   /* Length of message */
  __u16 nlmsg_type;  /* Message type. used by app, opaque to core. */
  __u16 nlmsg_flags; /* Additional flags */
  __u32 nlmsg_seq;   /* Sequence number. used by app, opaque to core. */
  __u32 nlmsg_pid;   /* Sending process PID. used by app, opaque to core. */
};
"""

nlmsghdr = '!LHHLL'

nl_sock = socket.socket(socket.AF_NETLINK, socket.SOCK_RAW)
