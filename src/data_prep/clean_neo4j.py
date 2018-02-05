# @name: clean_neo4j.py
# @description:  Pythonization of R code to prep neo4j outputs for input into a D3 bar graph/Sankey diagram
#                R code: https://github.com/flaneuse/ngly1-exploration/blob/master/R/exploration2.Rmd
# @author: Laura Hughes
# @email: lhughes@scripps.edu
# @date: 2 February 2018

# What this function does:
# 1. queries neo4j graph dataset to find connections for a paritcular query
# 2. pulls out the pertinent info for the nodes
# 3. merges annotation ontology terms with the nodes (not yet implemented)
# 4. pulls out the edge connections for each specific path number
# 5. combines nodes and edges into a json file and exports.
# 6. builds helper function to count number of metapaths

# neo4j query interface modified from https://github.com/NuriaQueralt/hypothesis-generation/blob/master/neo4j-hypotheses/q1_1_cypher_to_hypotheses.py

# setup
import pandas as pd
import json
import os
from neo4j.v1 import GraphDatabase, basic_auth

datain_dir = 'datain/neo4j/'
dataout_dir = 'dataout'

# Ideal data structure
# NODES:
#   *path_num*     unique id to identify the unique path between the nodes
#   *node_order*   number corresponding to node order within the path. 0 == source; N == target
#   *node_id*      unique id for the particular node (e.g. NCBIGene:1071)
#   *node_name*    name of node (e.g. CETP)
#   *node_type*    type of node (e.g. GENE)
#   *ont_terms*    nested object containing ontology term id, name, description, synonyms, iri url, and level in ancestry (0 is root), ontology id
# EDGES:
#   *path_num*     unique id to identify the unique path between the nodes
#   *edge_order*   number corresponding to edge order within the path. 0 == first link from source; N-1 == last link to target   [NOT NEEDED?]
#   *source_id*    unique id for the source node
#   *target_id*    unqiue id for the target node
#   *edge_type*    how terms are related (e.g. 'genetic association')
#   *edge_url*     url for the source for the edge relationship

# JSON output from neo4j, when returning path:
# 'data'
#   [arrayed for each separate path] --> path_num
#   'row': interleaved nodes and edges, sorted by their order in the path. --> easiest way to get the node_order, edge_order
#   'meta': metadata abt each node/edge in row.
#   'graph': unordered list of nodes/edges
# 'columns' --> name of return obj; in this case, just 'path'
# 'stats' --> description of paths

# More complicated structure than the output of the neo4j python package, which spits out an enumerator of the structure:
# - array of data['path']. within that:
#   - an array of nodes
#   - an array of edges
#   ... each with various params/structures, which are all nested objects.


# neo4j query
queries = {
"NGLY1-ENGASE":
"MATCH path=(source:GENE)-[:`RO:HOM0000020`]-(:GENE)--(ds:DISO)--(:GENE)-[:`RO:HOM0000020`]-(g1:GENE)--(pw:PHYS)--(target:GENE) WHERE source.id = 'NCBIGene:55768' AND target.id = 'NCBIGene:64772' AND ALL(x IN nodes(path) WHERE single(y IN nodes(path) WHERE y = x)) WITH g1, ds, pw, path, size( (source)-[:`RO:HOM0000020`]-() ) AS source_ortho, size( (g1)-[:`RO:HOM0000020`]-() ) AS other_ortho, max(size( (pw)-[]-() )) AS pwDegree, max(size( (ds)-[]-() )) AS dsDegree, [n IN nodes(path) WHERE n.preflabel IN ['cytoplasm','cytosol','nucleus','metabolism','membrane','protein binding','visible','viable','phenotype']] AS nodes_marked, [r IN relationships(path) WHERE r.property_label IN ['interacts with','in paralogy relationship with','in orthology relationship with','colocalizes with']] AS edges_marked WHERE size(nodes_marked) = 0 AND size(edges_marked) = 0 AND pwDegree < 51 AND dsDegree < 21 RETURN path",

"NFE2L1-AQP1":
"MATCH path=(source:GENE)-[:`RO:HOM0000020`]-(:GENE)--(ds:DISO)--(:GENE)-[:`RO:HOM0000020`]-(g1:GENE)--(pw:PHYS)--(target:GENE) WHERE source.id = 'NCBIGene:4779' AND target.id = 'NCBIGene:358' AND ALL(x IN nodes(path) WHERE single(y IN nodes(path) WHERE y = x)) WITH g1, ds, pw, path, size( (source)-[:`RO:HOM0000020`]-() ) AS source_ortho, size( (g1)-[:`RO:HOM0000020`]-() ) AS other_ortho, max(size( (pw)-[]-() )) AS pwDegree, max(size( (ds)-[]-() )) AS dsDegree, [n IN nodes(path) WHERE n.preflabel IN ['cytoplasm','cytosol','nucleus','metabolism','membrane','protein binding','visible','viable','phenotype']] AS nodes_marked, [r IN relationships(path) WHERE r.property_label IN ['interacts with','in paralogy relationship with','in orthology relationship with','colocalizes with']] AS edges_marked WHERE size(nodes_marked) = 0 AND size(edges_marked) = 0 AND pwDegree < 51 AND dsDegree < 21 RETURN path",

"NGLY1 - AQP1":
"MATCH path=(source:GENE)-[:`RO:HOM0000020`]-(:GENE)--(ds:DISO)--(:GENE)-[:`RO:HOM0000020`]-(g1:GENE)--(pw:PHYS)--(target:GENE) WHERE source.id = 'NCBIGene:55768' AND target.id = 'NCBIGene:358' AND ALL(x IN nodes(path) WHERE single(y IN nodes(path) WHERE y = x)) WITH g1, ds, pw, path, size( (source)-[:`RO:HOM0000020`]-() ) AS source_ortho, size( (g1)-[:`RO:HOM0000020`]-() ) AS other_ortho, max(size( (pw)-[]-() )) AS pwDegree, max(size( (ds)-[]-() )) AS dsDegree, [n IN nodes(path) WHERE n.preflabel IN ['cytoplasm','cytosol','nucleus','metabolism','membrane','protein binding','visible','viable','phenotype']] AS nodes_marked, [r IN relationships(path) WHERE r.property_label IN ['interacts with','in paralogy relationship with','in orthology relationship with','colocalizes with']] AS edges_marked WHERE size(nodes_marked) = 0 AND size(edges_marked) = 0 AND pwDegree < 51 AND dsDegree < 21 RETURN path"
}

# <<< query_neo4j(query, url = '52.87.232.110', port = '7688', username = "neo4j", pw = "sulabngly1testing") >>>
# main function to access the neo4j api to query network and return results
# inputs:   query string (Cypher query arguments)
#           url to local or AWS instance of network
#           port: location of port to access data; must also be opened on AWS
#           username/pw: access rights to the network
# output:   list containing flat dataframe of nodes and edges
def query_neo4j(query, url = '52.87.232.110', port = '7688', username = "neo4j", pw = "sulabngly1testing"):
    # initialize neo4j
    # requires bolt connection to the URI
    # port must be 7687: first instance of NGLY1 graph
    # or 7688: second instance of NGLY1 graph (and ports must be open in AWS)
    driver = GraphDatabase.driver(uri = "bolt://" + url + ":" + port, auth = (username, pw))

    # ask the driver object for a new session & run query
    # returns an enumerator
    with driver.session() as session:
        result = session.run(query)

    # parse query results
    # output = list()
    nodes = []
    edges = []
    path_num = 0

    for record in result:
        path_dct = parsePath(record, path_num)
        if (len(nodes) == 0): # first iteration of loop
            nodes = path_dct['nodes']
            edges = path_dct['edges']
        else:
            nodes = nodes.append(path_dct['nodes'], ignore_index=True)
            edges = edges.append(path_dct['edges'], ignore_index=True)
        path_num += 1

    return {'nodes': nodes, 'edges': edges}
        # if (path_num % 10 == 0):
            # print("Processed " + str(path_num) + "\n")

# <<< parsePath(path, path_num) >>>
# Core function to parse neo4j results for an individual path
# Pulling out the terms needed to interface with d3-based visualizations
# returns an object containing a dataframe of nodes and a dataframe of edges
def parsePath(path, path_num):
    # initialize vars
    # out = {}
    nodes = []
    edges = []
    n_counter = 0
    e_counter = 0

    # extract nodes
    # node objects contain: id, labels, properties(preflabel, description, id)
    for node in path['path'].nodes:
        n = {}

        n['path_num'] = path_num
        n['node_order'] = n_counter
        n['id'] = node.id # unique id generated by neo4j, used to link to relationships
        n['node_type'] = list(node.labels)[0]
        n['node_id'] = node.properties['id'] # unique id for node, used to link to ontologies
        n['node_name'] = node.properties['preflabel']

        nodes.append(n)
        n_counter += 1
    # extract edges
    # edge objects contain: id, start, end, type, properties(property_description, property_label, reference_uri, reference_date, reference_supporting_text, property_uri)
    for edge in path['path'].relationships:
        e = {}

        e['edge_order'] = e_counter
        e['path_num'] = path_num
        e['source_id'] = edge.start
        e['target_id'] = edge.end
        e['edge_type'] = edge.properties['property_label']
        e['edge_url'] = edge.properties['reference_uri']

        edges.append(e)
        e_counter += 1

    nodes = pd.DataFrame(nodes)
    edges = pd.DataFrame(edges)

    return {'nodes': nodes, 'edges': edges}

# run the queries
data = {}
for key, query in queries.items():
    print("querying " + key)
    data[key] = query_neo4j(query)


# <<< count_metapaths(data) >>>
# compress down nodes into a count of metapaths
# takes a list of nodes and edges and returns a count of node types
# NOTE: ignores any variation in the verb connecting the terms, e.g. an "is a" relationship versus a "part of" relationship
def count_metapaths(data):
    # compress each list of nodes per path down to a metapath: a single string of node_types per path_num
    # group by path_num and paste/concatenate together the node_types, separated by a hyphen
    paths = data['nodes'].groupby('path_num')['node_type'].apply(lambda x: '-'.join(x))
    # group by the metapaths
    # reset index so there's an additional column containing the path numbers; needed to count the number of paths of each type.
    return pd.DataFrame(paths).reset_index().groupby('node_type').agg('count')

# Pull out metapaths for all the queries
metapaths = []
for key, nodes in data.items():
    metapath = count_metapaths(nodes)
    metapath['query'] = key

    if(len(metapaths) == 0):
        metapaths = metapath
    else:
        metapaths = pd.concat([metapath, metapaths])
