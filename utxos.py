#!/usr/bin/python
# coding: utf8

# 从未花费的输入列表中选择最优输入
# 返回输入列表
# 目前没有用到
def select_outputs(unspent, min_value):
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