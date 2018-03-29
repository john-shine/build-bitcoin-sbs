#!/usr/bin/python
# coding: utf8

from constants import *
import struct
import utxos
import sign
import sys
import base58
import hashlib
import ecdsa
import json
import time
from RPC import RPCServer
from binascii import hexlify,unhexlify
from decimal import Decimal

def main():
    # 生成一个P2PKH地址
    rpc_server = RPCServer(TESTNET_SERVICE_URL)
    if not ('WALLET_ADDRESS' in globals()) or not isinstance(WALLET_ADDRESS, str) :
        try:
            bitcoin_address = rpc_server.getnewaddress('', 'legacy')
        except Exception as e:
            sys.exit('failure to get new address: %s' % str(e))

        print('new legacy bitcoin address (b58check) is: ', bitcoin_address)
    else:
        print('Your legacy bitcoin address (b58check) is: ', WALLET_ADDRESS)
        bitcoin_address = WALLET_ADDRESS
    # 获取到私钥
    rpc_server.walletpassphrase(WALLET_PASSPHRASE, 30)
    private_key = rpc_server.dumpprivkey(bitcoin_address)
    print("Your Private Key (WIF Format) is: ", private_key)
    # 获取公钥
    address_info = rpc_server.getaddressinfo(bitcoin_address)
    predict_public_key = address_info['pubkey']
    # 生成公钥，hex格式，压缩
    public_key = sign.make_public_key(private_key)
    try:
        assert public_key == predict_public_key
    except:
        sys.exit('Public key is incorrect  : %s\nCompare correct pubkey is: %s' % (public_key, predict_public_key))

    print("Public Key Compressed (hex) is: ", public_key)
    pubkey_point = sign.uncompress_point_by_pubkey(public_key)
    uncompressed_public_key = sign.get_point_pubkey_uncompressed(pubkey_point)

    bitcoin_address_for_test = sign.make_bitcoin_address(public_key, '6f')
    try:
        assert bitcoin_address == bitcoin_address_for_test
    except:
        sys.exit('Bitcoin address is incorrect: %s\nCompare correct address   is: %s' % (bitcoin_address_for_test, bitcoin_address))

    is_validate = sign.validate_address(bitcoin_address)
    if not is_validate:
        sys.exit('Your bitcoin address: %s is invalid' % bitcoin_address)
    else:
        print('Your bitcoin address: %s validate success' % bitcoin_address)

    # 获取 UTXO
    uxs = rpc_server.listunspent(MINCONF, MAXCONF, [bitcoin_address])
 
    if not uxs:
        sys.exit('Cannot get any utxos: %s' % uxs)

    scriptSig = '00' # 临时脚本长度 0 bytes
    inputTransactionHash = []
    total_amount = 0
    for utx in uxs:
        inputTransactionHash.append({"txid": utx['txid'], "vout": utx['vout'], 
            "value": float(utx['amount'])})
        total_amount += utx['amount']

    send_to_address = rpc_server.getnewaddress('', 'legacy')
    # 0.1 fee
    send_amount = total_amount - Decimal(0.1)
    outputs = [{send_to_address: float(send_amount)}]
    predict_rawTransaction = rpc_server.createrawtransaction(inputTransactionHash, outputs, 0)
    print("bitcoin-cli -testnet createrawtransaction '" + json.dumps(inputTransactionHash) + "' '" + json.dumps(outputs) + "' 0")
    
    rawTransaction = makeRawTransaction(inputTransactionHash, scriptSig, outputs)

    # print(rawTransaction)

    real_rawTransction = rpc_server.createrawtransaction(inputTransactionHash, outputs, 0)
    try:
        assert rawTransaction == real_rawTransction
    except:
        sys.exit(' raw transaction is not correct: %s\nCompare correct raw transaction: %s' % (rawTransaction, real_rawTransction))

    print('raw transaction:', rawTransaction)
    scriptSig = base58.hash_to_scriptPubKey(bitcoin_address)
    address_info = rpc_server.getaddressinfo(bitcoin_address)
    real_scriptSig = address_info['scriptPubKey']

    try:
        assert scriptSig == real_scriptSig
    except:
        sys.exit('incorrect: %s\n  correct: %s' % (scriptSig, real_scriptSig))

    scriptSig = varstr(unhexlify(scriptSig)).hex()
    rawTransaction_for_sign = makeRawTransaction(inputTransactionHash, scriptSig, outputs)
    rawTransaction_for_sign += SIGN_ALL
    print('raw transaction for sign:', rawTransaction_for_sign)
    scriptSig = signRawTransaction(rawTransaction_for_sign, private_key)
    print('scriptSig:', scriptSig)

    signed_transaction = makeRawTransaction(inputTransactionHash, scriptSig, outputs)
    # bitcoin-cli -testnet signrawtransaction 020000000154142f1ee2d9bd92d86fa8b8b0771b2121a8b93f82c0906c31bc114470779ede0000000000ffffffff0180d06b75000000001976a91427edfe4107b827b1966c972019ec5bfeb2e3256488ac00000000
    print('final signed transaction:', signed_transaction)
    verifyTransactionSign(signed_transaction)

    try:
        send_txid = rpc_server.sendrawtransaction(signed_transaction)
    except Exception as e:
        sys.exit('Send rawTransaction failed: "%s"' % str(e))
    send_txid = '059ee0471e48904e66d8df8fbedc13c096671b746af52612a92f62fae8401953'
    print('Send rawTransaction success, txid: ', send_txid)
    while True:
        transaction = rpc_server.gettransaction(send_txid)
        confirmations = transaction['confirmations']
        print('transaction confirmations: ', confirmations)
        time.sleep(3)
        if confirmations > 3:
            print('transaction more than three times')
            break

# Make transaction from the inputs
# outputs is a list of [{outputAddress: redemptionSatoshis}]
def makeRawTransaction(inputTransactionHash, scriptSig, outputs):
    def makeOutput(data):
        for outputAddress, redemptionSatoshis in data.items():
            pass
        scriptSig = base58.hash_to_scriptPubKey(outputAddress)
        return (
            # 以satoshi为单位，所以要乘以10**6
            struct.pack("<Q", int(Decimal(str(redemptionSatoshis)) * 100000000)).hex() +
            '%02x' % len(unhexlify(scriptSig)) + 
            scriptSig
        )

    # hex str
    formattedOutputs = ''.join(map(makeOutput, outputs))

    ret = (VERSION + # 4 bytes version
        "%02x" % len(inputTransactionHash)) # varint for number of inputs
    for tx in inputTransactionHash:
        tx_hash = tx['txid']
        tx_index = tx['vout']
        ret += (
            unhexlify(tx_hash)[::-1].hex() + # reverse inputTransactionHash
            struct.pack('<L', tx_index).hex() +
            scriptSig + # scriptSig
            "ffffffff" # sequence
        )

    ret += ( #'%02x' % len(unhexlify(scriptSig)) + # script length
        "%02x" % len(outputs) + # number of outputs
        formattedOutputs +
        "00000000" # lockTime
    )

    return ret

def signRawTransaction(rawTransaction, private_key):
    # 双sha256
    double_hash = hashlib.sha256(hashlib.sha256(unhexlify(rawTransaction)).digest()).digest()
    # 使用私钥加密
    print('double hash:', double_hash.hex())
    decoded_secrect = base58.base58check_decode(private_key)
    # 私钥长度必定是32个字节
    # 新私钥33个字节需要去掉后面的区分位
    if len(decoded_secrect) > 32:
        decoded_secrect = decoded_secrect[1:]
    if len(decoded_secrect) > 32:
        decoded_secrect = decoded_secrect[:32 - len(decoded_secrect)]
    print('decoded_secrect:', decoded_secrect.hex())
    ECDSA_sign = ecdsa.SigningKey.from_string(decoded_secrect, curve=ecdsa.SECP256k1)
    DER_encode = ECDSA_sign.sign_digest(double_hash, sigencode=ecdsa.util.sigencode_der) + unhexlify(HASH_TYPE)
    print('der encode:', DER_encode.hex())
    # public_key: hex str
    public_key = sign.make_public_key(private_key)
    # public_key = '76a91427edfe4107b827b1966c972019ec5bfeb2e3256488ac'
    print('public key:', public_key)
    # scriptSig: hex str
    scriptSig = varstr(DER_encode).hex() + varstr(unhexlify(public_key)).hex()
    final_scriptSig = varstr(unhexlify(scriptSig)).hex()
    return final_scriptSig


# Returns byte string value, not hex string
def varint(n):
    if n < 0xfd:
        return struct.pack('<B', n)
    elif n < 0xffff:
        return struct.pack('<cH', '\xfd', n)
    elif n < 0xffffffff:
        return struct.pack('<cL', '\xfe', n)
    else:
        return struct.pack('<cQ', '\xff', n)

# Takes and returns byte string value, not hex string
def varstr(s: bytes) ->bytes:
    return varint(len(s)) + s

# param str txn: hex格式
def parseTxn(txn):
    first = txn[0:41 * 2]
    script_len = int(txn[41 * 2:42 * 2], 16)
    script = txn[42 * 2: 42 * 2 + 2 * script_en]
    sig_len = int(script[0:2], 16)
    sig = script[2:2 + sig_len * 2]
    pub_len = int(script[2 + sig_len * 2:2 + sig_len * 2 + 2], 16)
    pub = script[2 + sig_len * 2 + 2:]
            
    assert(len(pub) == pub_len*2)
    rest = txn[42 * 2 + 2 * script_len:]
    return [first, sig, pub, rest] 

# Substitutes the scriptPubKey into the transaction, appends SIGN_ALL to make the version
# of the transaction that can be signed
def getSignableTxn(parsed):
    first, sig, pub, rest = parsed
    inputAddr = base58.base58check_decode(sign.make_bitcoin_address(pub, ''))
    return first + "1976a914" + inputAddr.hex() + "88ac" + rest + SIGN_ALL

# Input is a hex-encoded, DER-encoded signature
# Output is a 64-byte hex-encoded signature
def derSigToHexSig(s):
    s, junk = ecdsa.der.remove_sequence(unhexlify(s))
    if junk != '':
        print('JUNK', junk.hex())

    assert(junk == b'')
    x, s = ecdsa.der.remove_integer(s)
    y, s = ecdsa.der.remove_integer(s)
    return '%064x%064x' % (x, y)

# 校验签名之后的交易数据格式
def verifyTransactionSign(txn):
    parsed_txn = parseTxn(txn)
    signable_txn = getSignableTxn(parsed_txn)
    assert parsed_txn[1][-2:] == '01' # hash type
    # @todo
    # hashToSign = hashlib.sha256(hashlib.sha256(unhexlify(signable_txn)).digest()).digest().hex()
    # sig = derSigToHexSig(parsed[1][:-2])
    # public_key = parsed[2]
    # vk = ecdsa.VerifyingKey.from_string(unhexlify(public_key[2:]), curve=ecdsa.SECP256k1)
    # assert(vk.verify_digest(unhexlify(sig), unhdexlify(hashToSign)))

if __name__ == '__main__':
    main()