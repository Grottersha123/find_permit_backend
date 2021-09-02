import json
import os
import re

from elasticsearch import helpers
from icecream import ic

from config import ROOT_DIR_MAIN


def load_synonym(path):
    with open(path, 'r') as f:
        synonym = json.load(f)
    return synonym


def create_synonym_all(res, others):
    for key in others:
        if 'replace' in key:
            obj = ' '.join(key.split(' ')[1:])
            inst = 'install ' + obj
            add = 'add ' + obj
            res[inst] = key
            res[add] = key
    for key in others:
        if 'install' in key:
            obj = ' '.join(key.split(' ')[1:])
            add = 'add ' + obj
            res[inst] = key
            res[add] = key
    return res


def create_synonym_onto(res, others):
    new_res = []
    synonym = set(res.values())
    for key in others:
        if key in synonym:
            onto = next((name for name, onto in res.items() if onto == key), None)
            new_res.append(onto)
            if 'install' in onto:
                obj = ' '.join(onto.split(' ')[1:])
                add = 'add ' + obj
                new_res.append(add)
            if 'replace' in onto:
                obj = ' '.join(onto.split(' ')[1:])
                inst = 'install ' + obj
                add = 'add ' + obj
                new_res.append(inst)
                new_res.append(add)
        if 'replace' in key:
            obj = ' '.join(key.split(' ')[1:])
            inst = 'install ' + obj
            add = 'add ' + obj
            new_res.append(inst)
            new_res.append(add)
        if 'install' in key:
            obj = ' '.join(key.split(' ')[1:])
            add = 'add ' + obj
            new_res.append(add)

    return set(new_res)


def find_elastic_synonym(ontology='', data=dict()):
    print(data)
    synonym_onto = data.get(ontology, ontology)
    return synonym_onto


def init_elastic_search(es, num=None, path=r'elastic_dump'):
    print('start')
    if not es.indices.exists(index="city_stat"):
        ic('start_init city_stat')
        path_2 = os.path.join(ROOT_DIR_MAIN, r'{}/city_statistic.json'.format(path))
        ic(path_2)
        load_db_bulk(path_2, es, index_elastic='city_stat')
        mapping_city(es)
    if not es.indices.exists(index="zip_stat"):
        ic('start_init zip_stat')
        path_2 = os.path.join(ROOT_DIR_MAIN, r'{}/zip_statistic.json'.format(path))
        ic(path_2)
        load_db_bulk(path_2, es, index_elastic='zip_stat')
        mapping_zip(es)
    if not es.indices.exists(index="city_stat_company"):
        ic('start_init city_stat_company')
        path_2 = os.path.join(ROOT_DIR_MAIN, r'{}/company_city.json'.format(path))
        ic(path_2)
        load_db_bulk(path_2, es, index_elastic='city_stat_company')
    if not es.indices.exists(index="zip_stat_company"):
        ic('start_init zip_stat_company')
        path_2 = os.path.join(ROOT_DIR_MAIN, r'{}/company_zip.json'.format(path))
        ic(path_2)
        load_db_bulk(path_2, es, index_elastic='zip_stat_company')

    if not es.indices.exists(index="zip_city"):
        ic('start_init zip_city')
        path_2 = os.path.join(ROOT_DIR_MAIN, r'{}/zip_city_id.json'.format(path))
        ic(path_2)
        load_db_bulk(path_2, es, index_elastic='zip_city')



def mapping_city(es):
    mapping = {
        "properties": {
            "scode": {
                "type": "text",
                "fielddata": True
            },
            "city": {
                "type": "text",
                "fielddata": True
            },
            "descCombOntology": {
                "type": "text",
                "fielddata": True
            }

        }
    }
    es.indices.put_mapping(
        index="city_stat",
        body=mapping
    )


def mapping_zip(es):
    mapping = {
        "properties": {
            "zip": {
                "type": "text",
                "fielddata": True
            },
            "descCombOntology": {
                "type": "text",
                "fielddata": True
            }

        }
    }
    es.indices.put_mapping(
        index="zip_stat",
        body=mapping
    )


def load_db_one(path_json, es, index=''):
    with open(path_json, "r") as read_file:
        data = json.load(read_file)
    # Send the data into es
    es.index(index=index, ignore=400,
             id=1, body=data)


def load_json(directory):
    " Use a generator, no need to load all in memory"
    if directory.endswith('.json'):
        with open(directory, 'r') as open_file:
            yield json.load(open_file)


def load_db_bulk(path_json, es, index_elastic=''):
    with open(path_json, "r") as read_file:
        data = json.load(read_file)
    for index, d in enumerate(data):
        d['_id'] = index
    helpers.bulk(es, data[:len(data) // 2], index=index_elastic, doc_type='my-type')
    helpers.bulk(es, data[len(data) // 2:len(data)], index=index_elastic, doc_type='my-type')


def load_db_query(path_json, es, index='', num=None):
    with open(path_json, "r") as read_file:
        data = json.load(read_file)
    for index_, d in enumerate(data[:num]):
        es.index(index=index, id=index_, body=d)

    del data


def search_city_stat(es, scode='', city='', ontology=''):
    print(ontology, city, scode)
    query = {
        "query": {
            "bool": {
                "must": [
                    {"term": {"descCombOntology.keyword": ontology}},
                    {"term": {"city.keyword": city}},
                    {"term": {"scode.keyword": scode}},
                ]
            }
        }
    }
    res = es.search(index='city_stat', size=1, body=query)
    print(res)
    if res['hits']['hits']:
        return res['hits']['hits'][0]['_source']
    else:
        return None


def search_city_onto(es, scode='', city=''):
    query = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {"term": {"city.keyword": city}},
                    {"term": {"scode.keyword": scode}},
                ]
            }
        },
        "aggs": {
            "ontologies": {
                "terms": {
                    "field": "descCombOntology.keyword",
                    "size": 100000
                }
            }
        }
    }
    res = es.search(index='city_stat', size=1, body=query)
    if res['hits']['hits']:
        return res
    else:
        return None

def search_zip_onto(es, zip=''):
    query = {
        "size": 0,
        "query": {
            "bool": {
                "must": [
                    {"term": {"zip.keyword": zip}}
                ]
            }
        },
        "aggs": {
            "ontologies": {
                "terms": {
                    "field": "descCombOntology.keyword",
                    "size": 100000
                }
            }
        }
    }
    res = es.search(index='zip_stat', size=1, body=query)
    if res['hits']['hits']:
        return res
    else:
        return None
def unique_company(companies):
    unique_comp = []
    companies_new = []
    for company in companies:
        if not company['_source']['contractorcompanyname'] in unique_comp:
            unique_comp.append(company['_source']['contractorcompanyname'])
            companies_new.append(company)
    return companies_new

def clean_company(companies):
    for company in companies:
        temp = re.sub('[^a-zA-Z.\s]+', '', company['_source']['contractorcompanyname']).strip()
        temp = temp.replace("ldt.", "")
        temp = temp.replace("inc.", "")
        company['_source']['contractorcompanyname'] = temp.upper()
    return companies

def search_zip_city(es, zip=1):
    query = {"query": {
        "term": {
            "zip": zip
        }
    }
    }
    res = es.search(index='zip_city', body=query)
    print(res)
    if res:
        return res['hits']['hits'][0]['_source']['sourcecity'], res['hits']['hits'][0]['_source']['sourcestate']
    else:
        return None



def search_city_stat_comp(es, id_=1):
    query = {"query": {
        "term": {
            "city_stat_id": id_
        }
    }
    }
    res = es.search(index='city_stat_company', body=query)
    return res['hits']['hits']


def select_all_cities(es):
    query = {
        "size": 0,
        "aggs": {
            "city_code": {
                "composite": {
                    "sources": [
                        {"city": {"terms": {"field": "city"}}},
                        {"scode": {"terms": {"field": "scode"}}}
                    ], "size": 10000
                }
            }
        }
    }
    res = es.search(index='city_stat', body=query)
    return res

def select_by_zip_in_city_onto(es, zip=1):
    city, scode = search_zip_city(es, zip)
    print(city, scode)
    return search_city_onto(es, city=city, scode=scode)

def search_by_zip_in_city(es, zip=1, ontology=''):
    city, scode = search_zip_city(es, zip)
    return search_city_stat(es, city=city, scode=scode, ontology=ontology)



def select_all_zip(es):
    query = {
        "size": 0,
        "aggs": {
            "zips": {
                "composite": {
                    "sources": [
                        {"zip": {"terms": {"field": "zip"}}},
                    ], "size": 10000
                }
            }
        }
    }
    res = es.search(index='zip_stat', body=query)
    return res


def select_all_ontology_zip(es):
    query = {
        "size": 0,
        "aggs": {
            "ontologies": {
                "terms": {"field": "descCombOntology.keyword", "size": 10000000}
            }
        }
    }
    res = es.search(index='zip_stat', body=query)
    return res


def select_all_ontology_city(es):
    query = {
        "size": 0,
        "aggs": {
            "ontologies": {
                "terms": {"field": "descCombOntology.keyword", "size": 100000}
            }
        }
    }
    res = es.search(index='city_stat', body=query)
    return res


def search_zip_stat(es, zip='', ontology=''):
    query = {"query":
                 {"bool":
                      {"must":
                           [
                               {"term": {"descCombOntology.keyword": ontology}},
                               {"term": {"zip.keyword": zip}}
                           ]
                      }
                 }
    }
    res = es.search(index='zip_stat', size=1, body=query)
    print(res)
    if res['hits']['hits']:
        return res['hits']['hits'][0]['_source']
    else:
        return None


def search_zip_stat_comp(es, id_=1):
    query = {"query": {
        "term": {
            "zip_stat_id": id_
        }
    }
    }
    res = es.search(index='zip_stat_company', body=query)
    return res['hits']['hits']

# if __name__ == '__main__':
#     path = r'/home/grotter/flask_app_findpermit/elastic_json/zip_statistic.json'
#     load_db_query(path, es)
