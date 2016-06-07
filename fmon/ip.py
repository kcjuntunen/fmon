import socket
import fcntl
import struct
import array

def get_ip_address(ifname):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        return socket.inet_ntoa(fcntl.ioctl(
            s.fileno(),
            0x8915,  #SIOCGIFADDR
            struct.pack(u'256s', bytes(ifname[:15].encode('utf-8'))))[20:24])

def all_interfaces():
    max_possible = 128
    bytes = max_possible * 32
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        names = array.array('B', b'\0' * bytes)
        outbytes = struct.unpack('iL', fcntl.ioctl(
            s.fileno(),
            0x8912,  # SIOCGIFCONF
            struct.pack('iL', bytes, names.buffer_info()[0])
        ))[0]
        namestr = names.tobytes()
        return [namestr[i:i+32].split(b'\0', 1)[0].decode('utf-8')
                for i in range(0, int(outbytes), 32)]
