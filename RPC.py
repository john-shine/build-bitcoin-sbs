# !/usr/bin/python
# coding:utf8

from constants import *

try:
    import http.client as httplib
except ImportError:
    import httplib

import base64
import json
from decimal import Decimal

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

def EncodeDecimal(o):
    if isinstance(o, Decimal):
        return float(round(o, 8))
    raise TypeError(repr(o) + " is not JSON serializable")

class RPCServer(object):
    __id_count = 0

    def __init__(self, service_url, service_name=None, timeout=HTTP_TIMEOUT, connection=None):
        self.__service_url = service_url
        self.__service_name = service_name
        self.__url = urlparse.urlparse(service_url)
        if self.__url.port is None:
            port = 80
        else:
            port = self.__url.port
        (user, passwd) = (self.__url.username, self.__url.password)
        try:
            user = user.encode('utf8')
        except AttributeError:
            pass
        try:
            passwd = passwd.encode('utf8')
        except AttributeError:
            pass
        authpair = user + b':' + passwd
        self.__auth_header = b'Basic ' + base64.b64encode(authpair)

        self.__timeout = timeout

        if connection:
            # Callables re-use the connection of the original proxy
            self.__conn = connection
        elif self.__url.scheme == 'https':
            self.__conn = httplib.HTTPSConnection(self.__url.hostname, port,
                                                  timeout=timeout)
        else:
            self.__conn = httplib.HTTPConnection(self.__url.hostname, port,
                                                 timeout=timeout)

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            # Python internal stuff
            raise AttributeError
        if self.__service_name is not None:
            name = "%s.%s" % (self.__service_name, name)
        return RPCServer(self.__service_url, name, self.__timeout, self.__conn)

    def __call__(self, *args):
        RPCServer.__id_count += 1
        if DEBUG:
            print("-%s-> %s %s" % (RPCServer.__id_count, self.__service_name, 
                json.dumps(args, default=EncodeDecimal)))
        postdata = json.dumps({'version': '1.1',
                               'method': self.__service_name,
                               'params': args,
                               'id': RPCServer.__id_count}, default=EncodeDecimal
                            )
        self.__conn.request('POST', self.__url.path, postdata,
                            {
                                'Host': self.__url.hostname,
                                'User-Agent': USER_AGENT,
                                'Authorization': self.__auth_header,
                                'Content-type': 'application/json'
                            })
        self.__conn.sock.settimeout(self.__timeout)

        response = self._get_response()
        if response.get('error') is not None:
            raise Exception(response['error'])
        elif 'result' not in response:
            raise Exception({
                'code': -343, 'message': 'missing JSON-RPC result'})
        
        return response['result']

    def batch_call(self, rpc_calls):
        """Batch RPC call.
           Pass array of arrays: [ [ "method", params... ], ... ]
           Returns array of results.
        """
        batch_data = []
        for rpc_call in rpc_calls:
            RPCServer.__id_count += 1
            m = rpc_call.pop(0)
            batch_data.append({"jsonrpc":"2.0", "method":m, "params":rpc_call, "id":RPCServer.__id_count})

        postdata = json.dumps(batch_data, default=EncodeDecimal)
        if DEBUG:
            print("--> " + postdata)
        self.__conn.request('POST', self.__url.path, postdata,
                            {
                                'Host': self.__url.hostname,
                                'User-Agent': USER_AGENT,
                                'Authorization': self.__auth_header,
                                'Content-type': 'application/json'
                            })
        results = []
        responses = self._get_response()
        if isinstance(responses, (dict,)):
            if ('error' in responses) and (responses['error'] is not None):
                raise Exception(responses['error'])
            raise Exception({
                'code': -32700, 'message': 'Parse error'})
        for response in responses:
            if response['error'] is not None:
                raise Exception(response['error'])
            elif 'result' not in response:
                raise Exception({
                    'code': -343, 'message': 'missing JSON-RPC result'})
            else:
                results.append(response['result'])
        return results

    def _get_response(self):
        http_response = self.__conn.getresponse()
        if http_response is None:
            raise Exception({'code': -342, 'message': 'missing HTTP response from server'})

        content_type = http_response.getheader('Content-Type')
        if content_type != 'application/json':
            raise Exception({'code': -342, 
                'message': 'non-JSON HTTP response with \'%i %s\' from server' % (http_response.status, http_response.reason)})

        responsedata = http_response.read().decode('utf8')
        response = json.loads(responsedata, parse_float=Decimal)
        if "error" in response and response["error"] is None:
            if DEBUG:
                print("<-%s- %s" % (response["id"], 
                    json.dumps(response["result"], default=EncodeDecimal)))
        else:
            if DEBUG:
                print("<-- " + responsedata)
        return response
