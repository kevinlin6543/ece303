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


BUFF = 256
MSS = 250


class TheBestSender(BogoSender):
    PCKG = 0
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
        for seg in self.splitter(self.TEST_DATA, self.MSS, self.PCKG):
            try:
                if not self.resend:
                    segment = Segment(checksum=0, seqnum=0, acknum=0, data=seg)
                    segment.seqnum = Segment.seqnum(self, self.seqnum, seg, self.MSS)
                    self.seqnum = segment.seqnum
                    segment.acknum = Segment.acknum(self, 1)
                    byteArray = bytearray([segment.checksum, segment.acknum, segment.seqnum])
                    byteArray += seg
                    segment.checksum = Segment.checkSum(self, byteArray)
                    byteArray[0] = segment.checksum  # update checksum to new calculated value
                    self.simulator.u_send(byteArray)
                while True:
                    receivedByteArray = self.simulator.u_receive()

                    if self.checkCheckSum(receivedByteArray):  # ack not corrupted
                        if len(receivedByteArray) == 3 or receivedByteArray[1] == self.seqnum:
                            self.packageSent = True
                            self.simulator.u_send(byteArray)
                        elif receivedByteArray[1] == (self.seqnum + len(seg)) % 256:  # no error
                            self.dupCount = 0
                            if self.timeout > 0.1:
                                self.timeout -= 0.1
                            self.simulator.sndr_socket.settimeout(self.timeout)
                            self.resend = False
                            break
                        else:  # error
                            self.simulator.u_send(byteArray)  # resend data
                    else:
                        self.simulator.u_send(byteArray)  # resend data
                        self.dupCount += 1
                        if self.dupCount == 3 and self.packageSent:
                            self.timeout *= 2
                            self.simulator.sndr_socket.settimeout(self.timeout)
                            self.dupCount = 0
                            if self.timeout > 10:
                                print("Timeout has occurred!")
                                exit()

            except socket.timeout:
                self.resend = True
                self.simulator.u_send(byteArray)
                self.dupCount += 1
                if self.dupCount >= 3:
                    self.dupCount = 0
                    self.timeout *= 2
                    self.simulator.sndr_socket.settimeout(self.timeout)
                    if self.timeout > 10:
                        print("Timeout has occurred!")
                        exit()


    def checkCheckSum(self, data):
            xorSum = ~data[0]
            for i in xrange(1, len(data)):
                xorSum ^= data[i]
            if xorSum == -1:
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


    @staticmethod
    def acknum(self, isSender):
        return 0 if isSender else (self.seqnum + MSS)

    @staticmethod
    def checkSum(self, data):
        byteData = bytearray(data)
        xorSum = 0
        for i in xrange(len(byteData)):
            xorSum = byteData[i] ^ xorSum
        return xorSum


if __name__ == "__main__":
    # test out BogoSender
    DATA = bytearray(sys.stdin.read())
    sndr = TheBestSender()
    sndr.send(DATA)
