import socket, struct

__doc__ = """
Linux/include/uapi/linux/tcp.h
http://lxr.free-electrons.com/source/include/uapi/linux/tcp.h#L148
    struct tcp_info
http://stackoverflow.com/a/18189190/41948
http://linux.die.net/man/7/tcp
"""



s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('www.google.com', 80))
s.send('GET / HTTP/1.1\r\n\r\n')
s.recv(1024)
a=struct.unpack("B"*7+"I"*24, s.getsockopt(socket.SOL_TCP, socket.TCP_INFO, 104))
b=['tcpi_state', 'tcpi_ca_state', 'tcpi_retransmits', 'tcpi_probes', 'tcpi_backoff', 'tcpi_options', 'tcpi_snd_wscale+tcpi_rcv_wscale', 'tcpi_rto', 'tcpi_ato', 'tcpi_snd_mss', 'tcpi_rcv_mss', 'tcpi_unacked', 'tcpi_sacked', 'tcpi_lost', 'tcpi_retrans', 'tcpi_fackets', 'tcpi_last_data_sent', 'tcpi_last_ack_sent   ', 'tcpi_last_data_recv', 'tcpi_last_ack_recv', 'tcpi_pmtu', 'tcpi_rcv_ssthresh', 'tcpi_rtt', 'tcpi_rttvar', 'tcpi_snd_ssthresh', 'tcpi_snd_cwnd', 'tcpi_advmss', 'tcpi_reordering', 'tcpi_rcv_rtt', 'tcpi_rcv_space', 'tcpi_total_retrans',] 
print '\r\n'.join('%s: %s' % x for x in zip(b, a))


import socket
s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('cachefly.cachefly.net', 80))
s.send('GET / HTTP/1.1\r\n\r\n')
s.recv(1024)
s.getsockopt(socket.SOL_TCP, socket.TCP_INFO, 104)
