
static int tcp_show_netlink(struct filter *f, FILE *dump_fp, int socktype)
{
    int fd;
    struct sockaddr_nl nladdr;
    struct {
        struct nlmsghdr nlh;
        struct inet_diag_req r;
    } req;
    char    *bc = NULL;
    int    bclen;
    struct msghdr msg;
    struct rtattr rta;
    char    buf[8192];
    struct iovec iov[3];

    if ((fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_INET_DIAG)) < 0)
        return -1;

    memset(&nladdr, 0, sizeof(nladdr));
    nladdr.nl_family = AF_NETLINK;

    req.nlh.nlmsg_len = sizeof(req);
    req.nlh.nlmsg_type = socktype;
    req.nlh.nlmsg_flags = NLM_F_ROOT|NLM_F_MATCH|NLM_F_REQUEST;
    req.nlh.nlmsg_pid = 0;
    req.nlh.nlmsg_seq = 123456;
    memset(&req.r, 0, sizeof(req.r));
    req.r.idiag_family = AF_INET;
    req.r.idiag_states = f->states;
    if (show_mem)
        req.r.idiag_ext |= (1<<(INET_DIAG_MEMINFO-1));

    if (show_tcpinfo) {
        req.r.idiag_ext |= (1<<(INET_DIAG_INFO-1));
        req.r.idiag_ext |= (1<<(INET_DIAG_VEGASINFO-1));
        req.r.idiag_ext |= (1<<(INET_DIAG_CONG-1));
    }

    iov[0] = (struct iovec){
        .iov_base = &req,
        .iov_len = sizeof(req)
    };
    if (f->f) {
        bclen = ssfilter_bytecompile(f->f, &bc);
        rta.rta_type = INET_DIAG_REQ_BYTECODE;
        rta.rta_len = RTA_LENGTH(bclen);
        iov[1] = (struct iovec){ &rta, sizeof(rta) };
        iov[2] = (struct iovec){ bc, bclen };
        req.nlh.nlmsg_len += RTA_LENGTH(bclen);
    }

    msg = (struct msghdr) {
        .msg_name = (void*)&nladdr,
        .msg_namelen = sizeof(nladdr),
        .msg_iov = iov,
        .msg_iovlen = f->f ? 3 : 1,
    };

    if (sendmsg(fd, &msg, 0) < 0)
        return -1;

    iov[0] = (struct iovec){
        .iov_base = buf,
        .iov_len = sizeof(buf)
    };

    while (1) {
        int status;
        struct nlmsghdr *h;

        msg = (struct msghdr) {
            (void*)&nladdr, sizeof(nladdr),
            iov,    1,
            NULL,    0,
            0
        };

        status = recvmsg(fd, &msg, 0);

        if (status < 0) {
            if (errno == EINTR)
                continue;
            perror("OVERRUN");
            continue;
        }
        if (status == 0) {
            fprintf(stderr, "EOF on netlink\n");
            return 0;
        }

        if (dump_fp)
            fwrite(buf, 1, NLMSG_ALIGN(status), dump_fp);

        h = (struct nlmsghdr*)buf;
        while (NLMSG_OK(h, status)) {
            int err;
            struct inet_diag_msg *r = NLMSG_DATA(h);

            if (/*h->nlmsg_pid != rth->local.nl_pid ||*/
                h->nlmsg_seq != 123456)
                goto skip_it;

            if (h->nlmsg_type == NLMSG_DONE)
                return 0;
            if (h->nlmsg_type == NLMSG_ERROR) {
                struct nlmsgerr *err = (struct nlmsgerr*)NLMSG_DATA(h);
                if (h->nlmsg_len < NLMSG_LENGTH(sizeof(struct nlmsgerr))) {
                    fprintf(stderr, "ERROR truncated\n");
                } else {
                    errno = -err->error;
                    perror("TCPDIAG answers");
                }
                return 0;
            }
            if (!dump_fp) {
                if (!(f->families & (1<<r->idiag_family))) {
                    h = NLMSG_NEXT(h, status);
                    continue;
                }
                err = tcp_show_sock(h, NULL);
                if (err < 0)
                    return err;
            }

skip_it:
            h = NLMSG_NEXT(h, status);
        }
        if (msg.msg_flags & MSG_TRUNC) {
            fprintf(stderr, "Message truncated\n");
            continue;
        }
        if (status) {
            fprintf(stderr, "!!!Remnant of size %d\n", status);
            exit(1);
        }
    }
    return 0;
}

static int tcp_show_netlink_file(struct filter *f)
{
    FILE    *fp;
    char    buf[8192];

    if ((fp = fopen(getenv("TCPDIAG_FILE"), "r")) == NULL) {
        perror("fopen($TCPDIAG_FILE)");
        return -1;
    }

    while (1) {
        int status, err;
        struct nlmsghdr *h = (struct nlmsghdr*)buf;

        status = fread(buf, 1, sizeof(*h), fp);
        if (status < 0) {
            perror("Reading header from $TCPDIAG_FILE");
            return -1;
        }
        if (status != sizeof(*h)) {
            perror("Unexpected EOF reading $TCPDIAG_FILE");
            return -1;
        }

        status = fread(h+1, 1, NLMSG_ALIGN(h->nlmsg_len-sizeof(*h)), fp);

        if (status < 0) {
            perror("Reading $TCPDIAG_FILE");
            return -1;
        }
        if (status + sizeof(*h) < h->nlmsg_len) {
            perror("Unexpected EOF reading $TCPDIAG_FILE");
            return -1;
        }

        /* The only legal exit point */
        if (h->nlmsg_type == NLMSG_DONE)
            return 0;

        if (h->nlmsg_type == NLMSG_ERROR) {
            struct nlmsgerr *err = (struct nlmsgerr*)NLMSG_DATA(h);
            if (h->nlmsg_len < NLMSG_LENGTH(sizeof(struct nlmsgerr))) {
                fprintf(stderr, "ERROR truncated\n");
            } else {
                errno = -err->error;
                perror("TCPDIAG answered");
            }
            return -1;
        }

        err = tcp_show_sock(h, f);
        if (err < 0)
            return err;
    }
}

static int tcp_show(struct filter *f, int socktype)
{
    FILE *fp = NULL;
    char *buf = NULL;
    int bufsize = 64*1024;

    dg_proto = TCP_PROTO;

    if (getenv("TCPDIAG_FILE"))
        return tcp_show_netlink_file(f);

    if (!getenv("PROC_NET_TCP") && !getenv("PROC_ROOT")
        && tcp_show_netlink(f, NULL, socktype) == 0)
        return 0;

    /* Sigh... We have to parse /proc/net/tcp... */


    /* Estimate amount of sockets and try to allocate
     * huge buffer to read all the table at one read.
     * Limit it by 16MB though. The assumption is: as soon as
     * kernel was able to hold information about N connections,
     * it is able to give us some memory for snapshot.
     */
    if (1) {
        int guess = slabstat.socks+slabstat.tcp_syns;
        if (f->states&(1<<SS_TIME_WAIT))
            guess += slabstat.tcp_tws;
        if (guess > (16*1024*1024)/128)
            guess = (16*1024*1024)/128;
        guess *= 128;
        if (guess > bufsize)
            bufsize = guess;
    }
    while (bufsize >= 64*1024) {
        if ((buf = malloc(bufsize)) != NULL)
            break;
        bufsize /= 2;
    }
    if (buf == NULL) {
        errno = ENOMEM;
        return -1;
    }

    if (f->families & (1<<AF_INET)) {
        if ((fp = net_tcp_open()) == NULL)
            goto outerr;

        setbuffer(fp, buf, bufsize);
        if (generic_record_read(fp, tcp_show_line, f, AF_INET))
            goto outerr;
        fclose(fp);
    }

    if ((f->families & (1<<AF_INET6)) &&
        (fp = net_tcp6_open()) != NULL) {
        setbuffer(fp, buf, bufsize);
        if (generic_record_read(fp, tcp_show_line, f, AF_INET6))
            goto outerr;
        fclose(fp);
    }

    free(buf);
    return 0;

outerr:
    do {
        int saved_errno = errno;
        if (buf)
            free(buf);
        if (fp)
            fclose(fp);
        errno = saved_errno;
        return -1;
    } while (0);
}
