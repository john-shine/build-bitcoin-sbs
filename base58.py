#!/usr/bin/python
# coding: utf8
from binascii import hexlify, unhexlify, b2a_hex
import hashlib
import struct
import pdb

alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
len58 = len(alphabet)

def base58_encode(numberic: int) ->str:
    ret = ''
    numberic = int(numberic)
    if numberic < 0:
        return ret

    while numberic > 0:
        ret += alphabet[numberic % len58]
        numberic //= len58

    # reverse squence
    return ret[::-1]

def base58_decode(string: str) ->int:
    ret = 0
    # reverse string
    string = string[::-1]
    for i, s in enumerate(string):
        index = alphabet.index(s)
        ret += index * (len58 ** i)

    return ret

#
def base58check_encode(Bytes: bytes):
    # 编码的过程

    # 2 - Add a 0x80 byte in front of it for mainnet addresses or 0xef for testnet addresses. Also add a 0x01 byte at the end if the private key will correspond to a compressed public key
 
    # 3 - Perform SHA-256 hash on the extended key
    # 800C28FCA386C7A227600B2FE50B7CAE11EC86D3BF1FBE471BE89827E19D72AA1D

    # 4 - Perform SHA-256 hash on result of SHA-256 hash
    # 8147786C4D15106333BF278D71DADAF1079EF2D2440A4DDE37D747DED5403592

    # 5 - Take the first 4 bytes of the second SHA-256 hash, this is the checksum
    # 507A5B8DFED0FC6FE8801743720CEDEC06AA5C6FCA72B07C49964492FB98A714

    #    507A5B8D
    # 6 - Add the 4 checksum bytes from point 5 at the end of the extended key from point 2

    #    800C28FCA386C7A227600B2FE50B7CAE11EC86D3BF1FBE471BE89827E19D72AA1D507A5B8D
    #    800c28fca386c7a227600b2fe50b7cae11ec86d3bf1fbe471be89827e19d72aa1d507a5b8d
    # 7 - Convert the result from a byte string into a base58 string using Base58Check encoding. This is the Wallet Import Format

    #    5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ
    check_sum = hashlib.sha256(hashlib.sha256(Bytes).digest()).digest()
    r = Bytes + check_sum[:4]
    return base58_encode(int.from_bytes(r, byteorder='big'))

def base58check_decode(string: str) ->bytes:
    one_more_times = len(string) - len(string.lstrip('1'))
    decimal = base58_decode(string) # type: int
    all_bytes = bytes().fromhex(hex(decimal).lstrip('0x').rstrip('L'))
    # 4字节的check_sum
    ret, check_sum = all_bytes[:-4], all_bytes[-4:]
    # @todo 加版本前缀？
    ret_check = bytes().fromhex('00') * one_more_times + ret
    # 双sha256后的前4个字节
    real_check_sum =  hashlib.sha256(hashlib.sha256(ret_check).digest()).digest()[:4]
    assert(check_sum == real_check_sum)
    return ret[one_more_times:]

def hash_to_scriptPubKey(b58str):
    assert(len(b58str) == 34)
    decoded_b58str = base58check_decode(b58str)
    # 76     A9      14 (20 bytes)  
    if len(decoded_b58str) > 20:
        decoded_b58str = decoded_b58str[1:]
    if len(decoded_b58str) > 20:
        decoded_b58str = decoded_b58str[:20 - len(decoded_b58str)]
    # 测试网络需要去掉\x6f                            88             AC
    return '76a914' + decoded_b58str.hex() + '88ac'

if __name__ == '__main__':
    print(base58check_decode('2Myz4PFLijNPUquXonEcPMRXjDx6UiJGVbw').hex())
