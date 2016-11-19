"""
Python Code for Connecting a Node to TheThingsNetwork
for Microchip LoRaMOTE USA Version

Copyright (c) 2016 Jason Biegel, Chris Merck
All Rights Reserved

Modifications OTAA and ABP by Andres Sabas @ 16/Nov/2016

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import serial
import time
import sys

BAUD_RATE = 57600

class LoRaSerial(object):
    def __init__(self,_serial_port):
        '''
           configures serial connection
       '''
        self._ser = serial.Serial(_serial_port, BAUD_RATE)

        # timeout block read
        self._ser.timeout = 8

        # disable software flow control
        self._ser.xonxoff = False

        # disable hardware (RTS/CTS) flow control
        self._ser.rtscts = False

        # disable hardware (DSR/DTR) flow control
        self._ser.dsrdtr = False

        # timeout for write
        self._ser.writeTimeout = 0

        print "Resetting LoRa Tranceiver..."
        self.write_command('sys reset',False)
        print "Configuring Tranceiver..."
        self.write_command('mac set deveui 0012000000000001')
        self.write_command('mac set appeui 70B3D57ED0000DD4')
        self.write_command('mac set appkey DA145A04BF6882E95DB8CCAD4728140F')
        self.write_command('mac set dr 3')
        self.write_command('mac set adr off')
        self.write_command('mac set ar off')
        self.write_command('mac set sync 34')

#        FSB 1 (aka block A) =  0,  1,  2,  3,  4,  5,  6,  7 (125 kHz channels) plus 64 (500 kHz channel)
#        FSB 2 (aka block B) =  8,  9, 10, 11, 12, 13, 14, 15 plus 65
#        FSB 3 (aka block C) = 16, 17, 18, 19, 20, 21, 22, 23 plus 66
#        ....
#        FSB 7 (aka block G) = 48, 49, 50, 51, 52, 53, 54, 55 plus 70
#        FSB 8 (aka block H) = 56, 57, 58, 59, 60, 61, 62, 63 plus 71
        # configure sub-band 7
        for ch in range(0,72):
          self.write_command('mac set ch status %d %s'%(ch,
            'on' if ch in range(49,51+1) else 'off'))

        # configure plus 70
        self.write_command('mac set ch status 70 on')

        #save configuration
        self.write_command('mac save')

        # join the network
        print "Attempting to Join Network..."
        self.write_command('mac join otaa')
        response = self.read()
        if response == 'accepted':
          print "LoRa Tranceiver Configured."
        else:
          print "ERROR: mac join returned unexpected response: ", response

    def read(self):
        '''
           reads serial input
       '''
        return self._ser.readline().strip()

    def write(self, str):
        '''
           writes out string to serial connection, returns response
       '''
        self._ser.write(str + '\r\n')
        return self.read()

    def write_command(self, config_str, check_resp=False):
        '''
           writes out a command
       '''
        #print "Command: '%s'"%config_str
        response = self.write(config_str)
        if check_resp and response != 'ok':
          print "ERROR: Unexpected response: '%s'"%response

    def send_message(self, data):
        '''
           sends a message to backend via gateway
       '''
        print "Sending message: ", data
        print "in channel: ", channel
        # send packet (returns 'ok' immediately)
        self.write_command('mac tx uncnf %s %s'%(channel, data))
        # wait for success message
        response = self.read()
        if response == 'mac_tx_ok':
          print "Message sent successfully!"
        else:
          print "ERROR: mac tx command returned unexpected response: ", response

    def receive_message(self):
        '''
           waits for a message
       '''
        pass


if __name__ == "__main__":
  if len(sys.argv) < 4:
    print "Usage: python lora_mote_send_otaa.py <port> <data_hex> <channel>"
    print
    print "Example: python lora_mote_send_otaa.py /dev/ttyACM0 DEADBEEF 50"
    print "  Sends a LoRaWAN packet with four-byte payload {0xDE, 0xAD, 0xBE, 0xEF},"
    print "   using channel 50."
    print
    exit(0)

  port = sys.argv[1]
  data_hex = sys.argv[2]
  channel = sys.argv[3]
  loramote = LoRaSerial(port)
  loramote.send_message(data_hex)
