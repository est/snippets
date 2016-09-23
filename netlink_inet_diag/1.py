import re
import socket
import struct
import pymnl
from pymnl.message import Message, Payload
from pymnl.nlsocket import Socket
s = Socket(pymnl.NETLINK_INET_DIAG)
s.bind(pymnl.nlsocket.SOCKET_AUTOPID, 0)

msg = Message()

TCPDIAG_GETSOCK = 18
msg.set_type(TCPDIAG_GETSOCK)

msg.set_flags(pymnl.message.NLM_F_REQUEST | pymnl.message.NLM_F_ROOT | pymnl.message.NLM_F_MATCH)
msg.set_portid = 0
msg.set_seq(123456)

INET_DIAG_NONE = 0
INET_DIAG_MEMINFO = 1
INET_DIAG_INFO = 2
INET_DIAG_VEGASINFO = 3
INET_DIAG_CONG = 4


class InetDiagReq(object):
    idiag_family = socket.AF_INET
    idiag_src_len = 0
    idiag_dst_len = 0
    idiag_ext = 0

    idiag_sport = 0
    idiag_dport = 0
    idiag_src = 0
    idiag_dst = 0
    idiag_if = 0
    idiag_cookie = 0

    idiag_states = 0
    idiag_dbs = 0

    def get_binary(self):
        return struct.pack(
            '!BBBB'  # idiag family addr
            'HHIILL'  # intdiagsockid
            'LL',  # states and tables
            self.idiag_family,
            self.idiag_src_len,
            self.idiag_dst_len,
            self.idiag_ext,

            self.idiag_sport,
            self.idiag_dport,
            self.idiag_src,
            self.idiag_dst,
            self.idiag_if,
            self.idiag_cookie,

            self.idiag_states,
            self.idiag_dbs)

inet_diag_req = InetDiagReq()
inet_diag_req.idiag_family = socket.AF_INET
inet_diag_req.idiag_states = 0xFF
inet_diag_req.idiag_ext = (1 << (INET_DIAG_INFO - 1)) | (1 << (INET_DIAG_VEGASINFO - 1)) | (1 << (INET_DIAG_CONG - 1))
msg.put_extra_header(inet_diag_req)
s.send(msg)
ret = s.recv(flags=socket.MSG_DONTWAIT)
s.close()
for m in ret:
    print m.get_errno(), m.get_errstr()
    print repr(m.get_payload().get_binary())
