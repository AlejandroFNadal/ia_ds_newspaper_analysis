# establish udp communication between two devices. Implement checks to see if packages have been dropped and ask for retransmittion fi they have.
# to do these checks, use a counter that has to increase monotonically. If it does not, ask for retransmittion.

import socket
import time

class Copilot:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))
        self.counter = 0
        self.received = 0
        self.last = time.time()

    def run(self):
        while True:
            data, addr = self.sock.recvfrom(1024)
            #print "received message:", data, "from", addr
            if int(data) == self.counter:
                self.counter += 1
                self.received += 1
                if self.received % 1000 == 0:
                    print "received", self.received, "in", time.time() - self.last, "seconds"
                    self.last = time.time()
            else:
                print "received", data, "expected", self.counter
                self.counter = int(data) + 1
            self.sock.sendto(str(self.counter), addr)
