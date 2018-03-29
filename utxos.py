#!/usr/bin/python
# coding: utf8
# 贪心算法从UTXO列表中选择输入

# 从未花费的输入列表中选择最优输入
# 返回输入列表，并吧其它改动发送到改动地址
def select_outputs_greedy(unspent, min_value):
	# 如果utxo是空表示失败
	if not unspent:
		return None

	# 分割成两个列表
	# 小于min_value列表
	lessers = [utxo for utxo in unspent if utxo.value < min_value]
	key_func = lambda utxo: utxo.value
	# 大于等于min_value列表
	greaters = [utxo for utxo in unspent if utxo.value >= min_value]
	if greaters:
		# 非空的话，寻找最小的greaters
		min_greater = min(greaters)
		change = min_greater.value - min_value

		return [min_greater], change

	# 没有找到greaters，重新尝试若干更小的
	# 从大到小排序，我们需要尽可能使用最小的输入量
	lessers.sort(key=key_func, reverse=True)
	result = []
	accum = 0

	for utxo in lessers:
		result.append(utxo)
		accum += utxo.value
		if accum >= min_value:
			change = accum - min_value
			return result, "Change: %d Satoshis" % change
	# not found
	return None, 0

# unspent = [
# 	OutputInfo("ebadfaa92f1fd29e2fe296eda702c48bd11ffd52313e986e99ddad9084062167", 1, 8000000),
# 	OutputInfo("6596fd070679de96e405d52b51b8e1d644029108ec4cbfe451454486796a1ecf", 0, 16050000),
# 	OutputInfo("b2affea89ff82557c60d635a2a3137b8f88f12ecec85082f7d0a1f82ee203ac4", 0, 10000000),
# 	OutputInfo("7dbc497969c7475e45d952c4a872e213fb15d45e5cd3473c386a71a1b0c136a1", 0, 25000000),
# 	OutputInfo("55ea01bd7e9afd3d3ab9790199e777d62a0709cf0725e80a7350fdb22d7b8ec6", 17, 5470541),
# 	OutputInfo("12b6a7934c1df821945ee9ee3b3326d07ca7a65fd6416ea44ce8c3db0c078c64", 0, 10000000),
# 	OutputInfo("7f42eda67921ee92eae5f79bd37c68c9cb859b899ce70dba68c48338857b7818", 0, 16100000),
# ]


# target = 55000000

# print "For transaction amount %d Satoshis (%f bitcoin) use: " % (target, target / 10.0**8)
# print select_outputs_greedy(unspent, target)A