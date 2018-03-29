#!/usr/bin/python
# coding: utf8

from constants import *
import hashlib
import RPC
import base58
import ecdsa
from binascii import unhexlify, hexlify

# 椭圆曲线相关
_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_a = 0x0000000000000000000000000000000000000000000000000000000000000000
_b = 0x0000000000000000000000000000000000000000000000000000000000000007

_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
_Gy = 0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8
_r = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

def gen_random_secret():
    random_char = lambda: chr(random.randint(0, 255))
    convert_to_int = lambda array: int("".join(array).encode("hex"), 16)
    byte_array = [random_char() for i in range(32)]

    return convert_to_int(byte_array)

""" 
私钥产生公钥
""" 
def sign(key):
    # K 公钥
    # k 私钥
    # G 是生成点
    K = k * G

def validate_address(bitcoin_address):
    proxy = RPC.RPCServer(TESTNET_SERVICE_URL)
    info = proxy.validateaddress(bitcoin_address)
    try:
        assert info['isvalid'] == True
    except:
        return False

    return True

def get_point_pubkey(point):
    # 奇偶数表示point是在x轴上面还是下面
    if point.y() & 1:
        # 奇数
        key = '03' + '%064x' % point.x()
    else:
        # 偶数
        key = '02' + '%064x' % point.x()

    # print(key)

    return key

def get_point_pubkey_uncompressed(point):
    key = '04'+ '%064x' % point.x() + '%064x' % point.y()

    return key

# :param public_key: str hex格式压缩公钥
def uncompress_point_by_pubkey(public_key):
    # remove prefix
    point_x = int(public_key[2:], 16)
    beta = pow(int(point_x * point_x * point_x + _a * point_x + _b), int((_p + 1) // 4), int(_p))
    if (beta + int(public_key[:2], 16)) % 2:
        point_y = _p - beta
    else:
        point_y = beta

    class point(object):
        def x():
            return point_x

        def y():
            return point_y

    return point

# :praram str private_key: WIF格式编码的私钥
# :return str: 压缩hex格式的公钥
def make_public_key(private_key) ->str:
    # wif compressed格式私钥需要下去掉第一字节0x80或0xEF得到32字节hex私钥
    decoded_secrect = base58.base58check_decode(private_key)
    # @todo 最后一个字节是什么
    # 已经验证这里没有问题
    hex_secret = decoded_secrect[1:][:-1]
    curve_secp256k1 = ecdsa.ellipticcurve.CurveFp(_p, _a, _b)
    generator_secp256k1 = ecdsa.ellipticcurve.Point(curve_secp256k1, _Gx, _Gy, _r)
    # 比特币生成点
    generator = generator_secp256k1
    point = int.from_bytes(hex_secret, byteorder='big') * generator

    # Get the public key point. 
    return get_point_pubkey(point)

# :param str public_key: hex格式公钥，压缩
# :param str prefix: 前缀, hex格式
# @todo public_key是否需要解压缩，各不相同吗
def make_bitcoin_address(public_key, prefix):
    ripemd160 = hashlib.new('ripemd160')
    ripemd160.update(hashlib.sha256(unhexlify(public_key)).digest())
    hash160 = ripemd160.digest()
    return base58.base58check_encode(unhexlify(prefix) + hash160)
    # return base58.base58check_encode(b'\x80' + bytes().fromhex('0C28FCA386C7A227600B2FE50B7CAE11EC86D3BF1FBE471BE89827E19D72AA1D'))
