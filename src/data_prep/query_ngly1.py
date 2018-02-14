# @name:        query_ngly1.py
# @title:       run (test) queries on NGLY1 knowledge graph
# @description: create sample queries to use in development of D3-visualizations of graph networks 
# @author:      Laura Hughes
# @email:       lhughes@scripps.edu
# @date:        13 February 2018

# [0] Setup ------------------------------------------------------------------------
import src.data_prep.clean_neo4j as neo4j  # path within Atom notebook
import pandas as pd
import time

output_dir = 'src/data/'

# [1] set up the queries --------------------------------------------------------------
queries = {
    "NGLY1-ENGASE_structured":
    "MATCH path=(source:GENE)-[:`RO:HOM0000020`]-(:GENE)--(ds:DISO)--(:GENE)-[:`RO:HOM0000020`]-(g1:GENE)--(pw:PHYS)--(target:GENE) WHERE source.id = 'NCBIGene:55768' AND target.id = 'NCBIGene:64772' AND ALL(x IN nodes(path) WHERE single(y IN nodes(path) WHERE y = x)) WITH g1, ds, pw, path, size( (source)-[:`RO:HOM0000020`]-() ) AS source_ortho, size( (g1)-[:`RO:HOM0000020`]-() ) AS other_ortho, max(size( (pw)-[]-() )) AS pwDegree, max(size( (ds)-[]-() )) AS dsDegree, [n IN nodes(path) WHERE n.preflabel IN ['cytoplasm','cytosol','nucleus','metabolism','membrane','protein binding','visible','viable','phenotype']] AS nodes_marked, [r IN relationships(path) WHERE r.property_label IN ['interacts with','in paralogy relationship with','in orthology relationship with','colocalizes with']] AS edges_marked WHERE size(nodes_marked) = 0 AND size(edges_marked) = 0 AND pwDegree < 51 AND dsDegree < 21 RETURN path",

    "NFE2L1-AQP1_structured":
    "MATCH path=(source:GENE)-[:`RO:HOM0000020`]-(:GENE)--(ds:DISO)--(:GENE)-[:`RO:HOM0000020`]-(g1:GENE)--(pw:PHYS)--(target:GENE) WHERE source.id = 'NCBIGene:4779' AND target.id = 'NCBIGene:358' AND ALL(x IN nodes(path) WHERE single(y IN nodes(path) WHERE y = x)) WITH g1, ds, pw, path, size( (source)-[:`RO:HOM0000020`]-() ) AS source_ortho, size( (g1)-[:`RO:HOM0000020`]-() ) AS other_ortho, max(size( (pw)-[]-() )) AS pwDegree, max(size( (ds)-[]-() )) AS dsDegree, [n IN nodes(path) WHERE n.preflabel IN ['cytoplasm','cytosol','nucleus','metabolism','membrane','protein binding','visible','viable','phenotype']] AS nodes_marked, [r IN relationships(path) WHERE r.property_label IN ['interacts with','in paralogy relationship with','in orthology relationship with','colocalizes with']] AS edges_marked WHERE size(nodes_marked) = 0 AND size(edges_marked) = 0 AND pwDegree < 51 AND dsDegree < 21 RETURN path",

    "NGLY1-AQP1_structured":
    "MATCH path=(source:GENE)-[:`RO:HOM0000020`]-(:GENE)--(ds:DISO)--(:GENE)-[:`RO:HOM0000020`]-(g1:GENE)--(pw:PHYS)--(target:GENE) WHERE source.id = 'NCBIGene:55768' AND target.id = 'NCBIGene:358' AND ALL(x IN nodes(path) WHERE single(y IN nodes(path) WHERE y = x)) WITH g1, ds, pw, path, size( (source)-[:`RO:HOM0000020`]-() ) AS source_ortho, size( (g1)-[:`RO:HOM0000020`]-() ) AS other_ortho, max(size( (pw)-[]-() )) AS pwDegree, max(size( (ds)-[]-() )) AS dsDegree, [n IN nodes(path) WHERE n.preflabel IN ['cytoplasm','cytosol','nucleus','metabolism','membrane','protein binding','visible','viable','phenotype']] AS nodes_marked, [r IN relationships(path) WHERE r.property_label IN ['interacts with','in paralogy relationship with','in orthology relationship with','colocalizes with']] AS edges_marked WHERE size(nodes_marked) = 0 AND size(edges_marked) = 0 AND pwDegree < 51 AND dsDegree < 21 RETURN path",

    "NGLY1:AQP1_3edges":
    "MATCH (source { id: 'NCBIGene:55768', preflabel: 'NGLY1'}), (target { id: 'NCBIGene:358', preflabel: 'AQP1'}), path=(source)-[*..3]-(target) WITH source, target, path, [r IN relationships(path) | type(r)] AS types RETURN path",

    "alacrima:pathway_2": "MATCH (source { id: 'HP:0000522', preflabel: 'Alacrima'}), path=(source:DISO)-[*..2]-(target:PHYS) WITH source, target, path, [r IN relationships(path) | type(r)] AS types RETURN path",

    "alacrima:pathway_3":
    "MATCH (source { id: 'HP:0000522', preflabel: 'Alacrima'}), path=(source:DISO)-[*..3]-(target:PHYS) WITH source, target, path, [r IN relationships(path) | type(r)] AS types RETURN path"}

# [2] run the queries --------------------------------------------------------------
data = {}

# sample times
# querying NGLY1-ENGASE_structured
# total time: 1.52sec
#
# querying NFE2L1-AQP1_structured
# total time: 16.26sec
#
# querying NGLY1-AQP1_structured
# total time: 14.81sec
#
# querying NGLY1:AQP1_3edges
# total time: 8.92sec
#
# querying alacrima:pathway_2
# total time: 1.52sec
#
# querying alacrima:pathway_3
# total time: 85.91sec

for key, query in queries.items():
    print("\nquerying " + key)
    t1 = time.time()
    data[key] = neo4j.get_paths(query)
    t2 = time.time()
    print('total time: ' + str(round(t2 - t1, ndigits=2)) + "sec")

neo4j.save_paths(data, 'path-queries.json', direc = output_dir)

# [3] Pull out metapaths for all the queries --------------------------------------------------------------
metapaths = pd.DataFrame()

for key, nodes in data.items():
    metapath = neo4j.count_metapaths(nodes)
    metapath['query'] = key
    metapaths = pd.concat([metapath, metapaths])

# export
metapaths.reset_index().to_json(output_dir + 'test-metapaths.json')
