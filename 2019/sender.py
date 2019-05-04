# Written by S. Mevawala, modified by D. Gitzel

import logging
import socket
import channelsimulator
import utils
import sys
import random


class Sender(object):

    def __init__(self, inbound_port=50006, outbound_port=50005, timeout=10, debug_level=logging.INFO):
        self.logger = utils.Logger(self.__class__.__name__, debug_level)

        self.inbound_port = inbound_port
        self.outbound_port = outbound_port
        self.simulator = channelsimulator.ChannelSimulator(inbound_port=inbound_port, outbound_port=outbound_port,
                                                           debug_level=debug_level)
        self.simulator.sndr_setup(timeout)
        self.simulator.rcvr_setup(timeout)

    def send(self, data):
        raise NotImplementedError("The base API class has no implementation. Please override and add your own.")


class BogoSender(Sender):

    def __init__(self):
        super(BogoSender, self).__init__()

    def send(self, data):
        self.logger.info("Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))
        while True:
            try:
                self.simulator.u_send(data)  # send data
                ack = self.simulator.u_receive()  # receive ACK
                self.logger.info("Got ACK from socket: {}".format(
                    ack.decode('ascii')))  # note that ASCII will only decode bytes in the range 0-127
                break
            except socket.timeout:
                pass


class TheBestSender(BogoSender):
    BUFF = 256
    MSS = 250
    PCKG = 0
    while seqnum == (BUFF - MSS):
        seqnum = random.randint(0, 255)
    j = 0
    k = MSS
    copyCount = 0
    pkgSent = False
    resend = False

    buf = bytearray(BUFF)
    bufStart = seqnum
    bufEnd = seqnum

    def __init__(self):
        super(TheBestSender, self).__init__()

    def send(self, data):
        self.logger.info(
            "Sending on port: {} and waiting for ACK on port: {}".format(self.outbound_port, self.inbound_port))

    def checkCheckSum(self, data):  # this function calulates the checkSum of the RECEIVED data
        xorSum = ~data[0]  # checkSum is at data[0]
        for i in xrange(1, len(data)):
            xorSum ^= data[i]
        if xorSum == -1:  # if xorSum is 11111111, the data is not corrupted
            return True
        else:
            return False


class Segment(object):
    def __init__(self, checksum=0, seqnum=0, acknum=0, data=[]):
        self.data = data
        self.seqnum = seqnum
        self.acknum = acknum
        self.checksum = checksum

    @staticmethod
    def seqnum(self, prevSeqNum, data, MSS):
        return (prevSeqNum + MSS)%256


if __name__ == "__main__":
    # test out BogoSender
    DATA = bytearray(sys.stdin.read())
    sndr = BogoSender()
    sndr.send(DATA)
