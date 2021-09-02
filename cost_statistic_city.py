import collections, functools, operator

from utils.utils_load import load_json, save_json


def average_cost(path):
    data = load_json(path)
    return data


def key_func(k):
    return k['descCombOntology']


# sort INFO data by 'company' key.

data = average_cost(r'D:\Git_project\FindPermit\FindPermit\flask_app_findpermit\elastic_dump\zip_statistic.json')
data = sorted(data, key=key_func)
from itertools import groupby
avg_data = []
for k, v_ in groupby(data,key=lambda x: x['descCombOntology']):
    print (k)
    v = list(v_)

    res_25 = sum([val['q_25'] for val in v])/ len(v)
    res_50 = sum([val['q_50'] for val in v])/ len(v)
    res_75 = sum([val['q_75'] for val in v])/ len(v)
    print(res_25, res_50,res_75)
    for res in v :
        res_25_comp = res['q_25'] - res_25
        res_50_comp = res['q_50'] - res_50
        res_75_comp = res['q_75'] - res_75
        if res_25_comp < 0 and res_50_comp < 0 and res_75_comp < 0:
            res['q_25'] = round(res['q_25'] + res_25, 2)
            res['q_50'] = round(res['q_50'] + res_50,2)
            res['q_75'] = round(res['q_75'] + res_75,2)
        avg_data.append(res)

print(avg_data)
save_json('new_zip_statistic.json',avg_data)