import socket,struct

def makeMask(n):
    "return a mask of n bits as a long integer"
    return (2L<<n-1) - 1

def dottedQuadToNum(ip):
    "convert decimal dotted quad string to long integer"
    return struct.unpack('I',socket.inet_aton(ip))[0]

def networkMask(ip,bits):
    "Convert a network address to a long integer"
    return dottedQuadToNum(ip) & makeMask(bits)

def addressInNetwork(ip,net):
   "Is an address in a network"
   return ip & net == net

def isAddressInNetwork(ip,net,bits):
   "Is an address in a network without having to call other stupid functions"
   return addressInNetwork(dottedQuadToNum(ip), networkMask(net, bits))

