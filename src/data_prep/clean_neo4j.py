# @name: clean_neo4j.py
# @title: Get data from neo4j network
# @description:  Pythonization of R code to prep neo4j outputs for input into a D3 bar graph/Sankey diagram
#                R code: https://github.com/flaneuse/ngly1-exploration/blob/master/R/exploration2.Rmd
#            What this function does:
#                1. queries neo4j graph dataset to find connections for a paritcular query
#                2. pulls out the pertinent info for the nodes
#                3. merges annotation ontology terms with the nodes (not yet implemented)
#                4. pulls out the edge connections for each specific path number
#                5. combines nodes and edges into a json file and exports.
#                6. builds helper function to count number of metapaths
#           neo4j query interface modified from https://github.com/NuriaQueralt/hypothesis-generation/blob/master/neo4j-hypotheses/q1_1_cypher_to_hypotheses.py
# @author: Laura Hughes
# @email: lhughes@scripps.edu
# @date: 2 February 2018



# setup
import pandas as pd
import json
import os
from neo4j.v1 import GraphDatabase, basic_auth

dataout_dir = 'src/data/'

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


# <<< query_neo4j(query, url = '52.87.232.110', port = '7688', username = "neo4j", pw = "sulabngly1testing") >>>
# main function to access the neo4j api to query network and return results
# inputs:   query string (Cypher query arguments)
#           url to local or AWS instance of network
#           port: location of port to access data; must also be opened on AWS
#           username/pw: access rights to the network
# output:   neo4j result enumerator
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

    return result

# <<< get_paths(query, url = '52.87.232.110', port = '7688', username = "neo4j", pw = "sulabngly1testing") >>>
# main function to access the neo4j api to query network and return results
# inputs:   query string (Cypher query arguments)
#           url to local or AWS instance of network
#           port: location of port to access data; must also be opened on AWS
#           username/pw: access rights to the network
# output:   list containing flat dataframe of nodes and edges
def get_paths(query, url = '52.87.232.110', port = '7688', username = "neo4j", pw = "sulabngly1testing"):
    # run query
    result = query_neo4j(query, url = '52.87.232.110', port = '7688', username = "neo4j", pw = "sulabngly1testing")

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

# <<< get_nodes(query = 'MATCH (n) RETURN *', url = '52.87.232.110', port = '7688', username = "neo4j", pw = "sulabngly1testing") >>>
# main function to access the neo4j api to query network and return results
# inputs:   query string (Cypher query arguments)
#           url to local or AWS instance of network
#           port: location of port to access data; must also be opened on AWS
#           username/pw: access rights to the network
# output:   flat dataframe of nodes
def get_nodes(query = 'MATCH (n) RETURN *', url = '52.87.232.110', port = '7688', username = "neo4j", pw = "sulabngly1testing", verbose = False):
    # run query
    result = query_neo4j(query, url = '52.87.232.110', port = '7688', username = "neo4j", pw = "sulabngly1testing")

    # parse query results
    nodes = parseNode(result, verbose)
    return nodes


# <<< parseNode(nodes) >>>
# Core function to parse neo4j results for an individual node
# Pulling out the terms needed to interface with ontology annotations
def parseNode(result, verbose = True):
    # initialize vars
    nodes = []

    # extract nodes
    # node objects contain: id, labels, properties(preflabel, description, id)
    for node in result:
        n = {}

        try:
            node['n'].properties['preflabel'] # unique id generated by neo4j, used to link to relationships
        except:
            if verbose:
                print('ignoring id ' + str(node['n'].id ))
        else:
            n['id'] = node['n'].id # unique id generated by neo4j, used to link to relationships
            n['node_type'] = list(node['n'].labels)[0]
            n['node_id'] = node['n'].properties['id'] # unique id for node, used to link to ontologies
            n['node_name'] = node['n'].properties['preflabel']
            n['description'] = node['n'].properties['description']

        nodes.append(n)

    nodes = pd.DataFrame(nodes).dropna(how='all')
    return nodes


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

def save_paths(data, filename, direc = dataout_dir):
    class JSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if hasattr(obj, 'to_json'):
                return obj.to_json(orient='records')
            return json.JSONEncoder.default(self, obj)

    with open(direc + '/' + filename, 'w') as outfile:
        json.dump(data, outfile, cls = JSONEncoder)

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
