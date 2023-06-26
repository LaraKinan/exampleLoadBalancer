# uncompyle6 version 3.9.0
# Python bytecode version base 2.7 (62211)
# Decompiled from: Python 3.9.8 (tags/v3.9.8:bb3fdcf, Nov  5 2021, 20:48:33) [MSC v.1929 64 bit (AMD64)]
# Embedded file name: ./exampleLB.py
# Compiled at: 2015-12-28 12:42:45
import socket, SocketServer, Queue, sys, time, threading
HTTP_PORT = 80
previous_server = 3
lock = threading.Lock()
SERV_HOST = '10.0.0.1'
servers = {'serv1': ('192.168.0.101', None), 'serv2': ('192.168.0.102', None), 'serv3': ('192.168.0.103', None)}
serverTimes = {'serv1' : ("V", 0), 'serv2' : ("V", 0), 'serv3' : ("M", 0)}

def LBPrint(string):
    print '%s: %s-----' % (time.strftime('%H:%M:%S', time.localtime(time.time())), string)


def createSocket(addr, port):
    for res in socket.getaddrinfo(addr, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        print("af ", af, " sockType ", socktype, " proto ", proto, " canonname ", canonname, " sa ", sa)
        try:
            new_sock = socket.socket(af, socktype, proto)
        except socket.error as msg:
            LBPrint(msg)
            new_sock = None
            continue

        try:
            new_sock.connect(sa)
        except socket.error as msg:
            LBPrint(msg)
            new_sock.close()
            new_sock = None
            continue

        break

    if new_sock is None:
        LBPrint('could not open socket')
        sys.exit(1)
    return new_sock


def getServerSocket(servID):
    name = 'serv%d' % servID
    return servers[name][1]


def getServerAddr(servID):
    name = 'serv%d' % servID
    return servers[name][0]


def getNextServer():
    global lock
    global previous_server
    lock.acquire()
    next_server = previous_server % 3 + 1
    previous_server = next_server
    lock.release()
    return next_server


def parseRequest(req):
    return (
     req[0], req[1])


class LoadBalancerRequestHandler(SocketServer.BaseRequestHandler):
    
    def expectedTime(self, servID, reqType, reqTime):
        if(serverTimes['serv%d' % servID][0] == 'M' and reqType == "V"):
            return 3*reqTime
        if((serverTimes['serv%d' % servID][0] == 'M' and reqType == "P") or (serverTimes['serv%d' % servID][0] == 'V' and reqType == "M")):
            return 2*reqTime
        return reqTime
    
    def expectedTotalTime(self, servID, reqType, reqTime):
        times = []
        for i in range(1, len(servers) + 1):
            if i == servID:
                times.append(serverTimes['serv%d' % i][1] + self.expectedTime(i, reqType, reqTime))
            else:
                times.append(serverTimes['serv%d' % i][1])
        return max(times)
    
    def decide(self, reqType, reqTime):
        max_times = []
        for i in range(1, len(servers) + 1):
            max_times.append((self.expectedTotalTime(i, reqType, reqTime)), i)
            print("The max for adding ", reqType,reqTime, " at ", i , " is ", max_times[i - 1])
        minServID, minTime = min(max_times)
        return minServID

    def handle(self):
        client_sock = self.request
        req = client_sock.recv(2)
        req_type, req_time = parseRequest(req)
        # servID = getNextServer() # TODO: Change to function that handles my algorithm : int decideServer(req_type, req_time, )
        servID = self.decide(req_type, req_time)
        LBPrint('recieved request %s from %s, sending to %s' % (req, self.client_address[0], getServerAddr(servID)))
        serv_sock = getServerSocket(servID)
        serv_sock.sendall(req)
        data = serv_sock.recv(2)
        client_sock.sendall(data)
        client_sock.close()


class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass


if __name__ == '__main__':
    try:
        LBPrint('LB Started')
        LBPrint('Connecting to servers')
        for name, (addr, sock) in servers.iteritems():
            new_socket = createSocket(addr, HTTP_PORT)
            servers[name] = (
             addr, new_socket)

        server = ThreadedTCPServer((SERV_HOST, HTTP_PORT), LoadBalancerRequestHandler)
        server.serve_forever()
    except socket.error as msg:
        LBPrint(msg)
# okay decompiling exampleLB.pyc
