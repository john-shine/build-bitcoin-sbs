# build-bitcoin-sbs
manually build Bitcoin step-by-step on binary

一步步创建比特币交易

主要分为一下步骤：
* base58check算法的实现
* 私钥转公钥+比特币地址
* 得到+选择input，构造output
* 由input+output+私钥构建交易
* 对交易签名得到scriptSig
* 拼接成签名的完整交易
* 广播交易到比特币p2p网络
