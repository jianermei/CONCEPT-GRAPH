# -*- coding: utf-8 -*-

from datetime import datetime
from SPARQLWrapper import SPARQLWrapper, JSON
import networkx as nx
import matplotlib.pyplot as plt


JP_DBPEDIA_URI = "http://swrenodept.dev.hon.olympus.co.jp:8890/sparql"


def log_time():
    print(datetime.now().strftime("%Y/%m/%d %H:%M:%S"))


def make_query(queryString):
    sparql = SPARQLWrapper(JP_DBPEDIA_URI)

    # log_time()
    sparql.setQuery(queryString)

    try:
        sparql.setReturnFormat(JSON)
        ret = sparql.query()
        results = ret.convert()

        # log_time()
        return results
    except Exception as e:
        # log_time()
        print("Something is wrong... ", e.args)


def get_wikipedia_resource():
    queryString = """
        SELECT DISTINCT ?s
        WHERE { 
            ?s ?p ?o .  
            FILTER REGEX(?s, "http://ja.dbpedia.org/resource") 
        }
    """

    # NOT completed! there are some subjects like "http://ja.dbpedia.org/resource/Category:XXX".

    results = make_query(queryString)
    print(len(results["results"]["bindings"]))

    f = open('dbpedia_results.txt', 'w')

    for result in results["results"]["bindings"]:
        # print(result["s"]["value"])
        f.write(result["s"]["value"])
        f.write("\n")

    f.close()

    # log_time()


def get_concept(word):
    queryString = """
        PREFIX dbp:<http://ja.dbpedia.org/resource/{0}>
        PREFIX dcterms:<http://purl.org/dc/terms/>
        SELECT ?o
        WHERE {{
          dbp: dcterms:subject ?o .
        }}
    """

    # print queryString.format(word.encode('utf-8'))

    results = make_query(queryString.format(word.encode('utf-8')))

    concepts = list()

    if results is None:
        return concepts

    for result in results["results"]["bindings"]:
        try:
            concept = result["o"]["value"].split(':')[2]
            # print("concept: " + concept)
            concepts.append(concept)
        except Exception as e:
            # log_time()
            print("Can not get concept... ", e.args)

    return concepts


def get_hierarchy(concept):
    # print("concept: " + concept)
    queryString = """
        PREFIX category-ja: <http://ja.dbpedia.org/resource/Category:{0}>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        SELECT ?o
        WHERE {{ 
          category-ja: skos:broader ?o . 
        }}
    """

    # print queryString.format(concept.encode('utf-8'))

    results = make_query(queryString.format(concept.encode('utf-8')))

    hierarchies = list()

    if results is None:
        return hierarchies

    for result in results["results"]["bindings"]:
        try:
            hierarchy = result["o"]["value"].split(':')[2]
            # print("hierarchy: " + hierarchy)
            hierarchies.append(hierarchy)
        except Exception as e:
            # log_time()
            print("Can not get hierarchy... ", e.args)

    return hierarchies


def get_hierarchies(concept, HG):
    hierarchies = get_hierarchy(concept)
    # log_time()

    # whether hierarchies is EMPTY
    if len(hierarchies) == 0:
        return HG

    for hierarchy in hierarchies:
        # check here!
        # whether hierarchy is already in GRAPH
        if hierarchy in HG:
            HG.add_edge(concept, hierarchy)
            continue

        HG.add_node(hierarchy)
        HG.add_edge(concept, hierarchy)

        sec_hierarchies = get_hierarchies(hierarchy, HG)
        HG.add_node(sec_hierarchies)

    return HG


def get_hierarchies_non_recursive(c, G):

    stack = [c, G]

    while len(stack) > 0:
        # print(stack)
        # print("stack depth: " + str(len(stack)))
        # print("number of current node: " + str(len(G.nodes(data=True))))
        c, G = stack[-2:]
        del stack[-2:]

        h = get_hierarchy(c)

        if len(h) == 0:
            # print("node from " + str(len(stack[-1].nodes(data=True))) + " to " + str(len(G.nodes(data=True))))
            del stack[-1:]
            stack.append(G)
        else:
            for n in h:
                if n in G:
                    continue
                G.add_node(n)
                G.add_edge(c, n)
                stack.extend([n, G])

    return G


def reprunicode(u):
    return repr(u).decode('raw_unicode_escape')


def show_graph_details(graph):
    print "Show details of graph..."
    print("Number of nodes: " + str(len(graph.nodes(data=True))))
    print("Number of edges: " + str(len(graph.edges(data=True))))

    for n in graph:
        print n

    for e in graph.edges(data=True):
        print u'[%s]' % u', '.join([u'(%s,)' % reprunicode(ti) for ti in e])

    plt.subplot(121)
    nx.draw(graph, with_labels=True, font_weight='bold', font_family='TakaoGothic')
    plt.show()
    pass


WikiG = nx.DiGraph()

word = u'東京都'
WikiG.add_node(word)
log_time()

print "Get concept..."
concepts = get_concept(word)
log_time()


print "Get hierarchies..."
for concept in concepts:
    WikiG.add_node(concept)
    WikiG.add_edge(word, concept)
    get_hierarchies(concept, WikiG)
    # WikiG = get_hierarchies_non_recursive(concept, WikiG)
    pass
log_time()


print "Save graph..."
nx.write_graphml(WikiG, 'WikipediaGraph.graphml', encoding='utf-8')
log_time()

# print "Loading graph..."
# WikiG = nx.read_graphml('WikipediaGraph.graphml', unicode)
