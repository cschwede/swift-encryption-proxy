#!/usr/bin/python
""" Copyright 2013 Christian Schwede <info@cschwede.de>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

"""
import os
import sys
from urllib import quote as urlquote

from Crypto.Cipher import AES
from twisted.python import log
from twisted.internet import reactor
from twisted.web import proxy, server


AES_KEY = 'NKdEl551YLlLUshx' # just a random value


def decrypt(data, aes_key):
    _iv = data[0:16]
    decryptor = AES.new(aes_key, AES.MODE_CBC, _iv)
    data = decryptor.decrypt(data[16:])
    padding_size = len(data) - ord(data[-1])
    return data[0:padding_size]


def encrypt(data, aes_key):
    _iv = os.urandom(16)
    encryptor = AES.new(aes_key, AES.MODE_CBC, _iv)
    pad = 16 - len(data) % 16
    data = data + pad * chr(pad)
    return _iv + encryptor.encrypt(data)


class ProxyClient(proxy.ProxyClient):
    global HOSTNAME
    
    def __init__(self, command, rest, version, headers, data, father):
        proxy.ProxyClient.__init__(self, command, rest, version, headers, data, father)
        self.down = []
        self.hostname = HOSTNAME

    def connectionMade(self):
        if self.father.method == 'PUT':
            self.data = encrypt(self.data, AES_KEY)
        self.sendCommand(self.command, self.rest)
        for header, value in self.headers.items():
            if self.father.method == 'PUT' and header == 'content-length':
                value = len(self.data)
            if header == 'host':
                value = self.hostname
            self.sendHeader(header, value)
        self.endHeaders()
        self.transport.write(self.data)

    def handleResponsePart(self, buffer):
        # Decryption is done once all data is downloaded from Swift
        self.down.append(buffer)

    def handleResponseEnd(self):
        if not self._finished:
            self._finished = True
            data = ''.join(self.down)
            if self.father.method == 'GET':
                try:
                    data = decrypt(data, AES_KEY)
                    self.father.responseHeaders.setRawHeaders('content-length', [str(len(data))])
                except ValueError:
                    pass
            self.father.write(data)
            self.father.finish()
            self.transport.loseConnection()


class ProxyClientFactory(proxy.ProxyClientFactory):
    protocol = ProxyClient


class ReverseProxyResource(proxy.ReverseProxyResource):
    proxyClientFactoryClass = ProxyClientFactory

    def getChild(self, path, request):
        return ReverseProxyResource(
            self.host, self.port, self.path + '/' + urlquote(path, safe=""),
            self.reactor)


if __name__ == '__main__':
    global HOSTNAME
    if len(sys.argv) < 2:
        exit("Missing hostname")
    HOSTNAME = sys.argv[1]
    log.startLogging(sys.stdout)
    site = server.Site(ReverseProxyResource(HOSTNAME, 8080, ''))
    reactor.listenTCP(8080, site)

    reactor.run()
