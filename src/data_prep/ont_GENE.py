# Pulls ontology tree from EBI's Ontology Lookup Service (OLS) API (https://www.ebi.ac.uk/ols/index);
# then parses into individual terms and creates the parents for each individual term.
# Laura Hughes, lhughes@scripps.edu, 31 January 2018
# Building in part off of python [ols-client library](https://github.com/cthoyt/ols-client/blob/master/src/ols_client/client.py)

# Setup
import numpy as np
import pandas as pd
import requests


# After looking through the documentation and all the associated fields that come out from the API call, it looks like there's no way to avoid
# doing a loop through the entire tree, starting from end node and iterating till you hit the root (s).
# Perhaps not the fastest way, but the most direct way will start from the end node rather than going from the roots down.
ont_id = 'go' # Gene ontology ID
ont_id = 'fbcv' # flybase controlled vocabulary

# <<< get_data(url) >>>
# Access data from EBI API
# returns json object with unfiltered layers of gooiness.
# General structure:
#   data['page'] --> list of number of pages in the full query
#   data['_links'] --> https request strings for first, next, last, self pages
#   data['_embedded']['terms'] --> nested list of the actual data for each term.  Incldues:
#     ...['_links']: https requests for ancestors, descendants, tree structure, graph structure for *each* term
#     ...['description']: short description of term
#     ...['iri']: permanent url to Ontobee page about term
#     ...['is_obsolete']: t/f if term is obsolete
#     ...['is-root']: t/f if is uppermost level
#     ...['label']: name of term
#     ...['obo_id']: unique id
#     ...['synonyms']: synonyms for term
#     ...[<other stuff>]: things that didn't seem as relevant.
def get_data(url):
    resp = requests.get(url)

    if (resp.ok):
        data = resp.json()
        return data
    else:
        print('query was not sucessful')
        return None

# <<< addit_pages(json_data) >>>
# Checks if previous call to OLS has more results
# returns the url for the next query if there are more pages
def addit_pages(json_data):
    curr_page = json_data['page']['number']
    last_page = json_data['page']['totalPages']-1

    if(curr_page < last_page):
        next_page = json_data['_links']['next']['href']
        return next_page
    else:
        return False

# <<< _term_gen(json_data) >>>
# term generator to be able to loop through all terms in pulled data
def _term_gen(data):
    for term in data['_embedded']['terms']:
        yield term

# <<< pull_terms(json_data) >>>
# function to remove only the good bits from an API call to OLS
# collects all the terms within a given ontology
# returns a dataframe containing their ids, labels (names), descriptions, synonyms, iri (purl to ontobee), whether is a root node, and the url to call to get their hierarchicalChildren
def pull_terms(json_data, filter_obs = True):
    iter_terms = _term_gen(json_data)

    ids = []
    labels = []
    descrips = []
    syn = []
    iri = []
    root = []

    # pull out the relevant values
    for term in iter_terms:
        # filter out the obsolete terms, if specified
        # removes:
        #   obsolete terms
        #   "Thing"
        if((not filter_obs) | ((not term['is_obsolete']) & pd.notnull(term['obo_id']))):
            ids.append(term['obo_id'])
            labels.append(term['label'])
            descrips.append(term['description'])
            syn.append(term['synonyms'])
            iri.append(term['iri'])
            root.append(term['is_root'])
    # convert to a dataframe
    terms = pd.DataFrame([ids, labels, descrips, syn, iri, root], index = ['id', 'label', 'description', 'synonyms', 'node_url', 'is_root']).T.set_index('id')

    return terms

# Primary API call to OLS to get the unique terms.
# returns terms, parents
def get_terms(ont_id, base_url = 'http://www.ebi.ac.uk/ols/api/ontologies/', end_url = '/terms?size=500', return_parents = True):
    url = base_url + ont_id + end_url

    json_data = get_data(url)

    # set up containers for loops
    terms = pull_terms(json_data)
    next_page = addit_pages(json_data)

    while(next_page):
        # print('calling API')
        json_data = get_data(next_page)
        next_page = addit_pages(json_data) # update next page

        terms = pd.concat([terms,pull_terms(json_data)])

    parents = None

    # return { 'terms': terms, 'parents': parents }
    return terms

# x = %timeit get_terms('go')


go = get_terms('go')

go.shape
# [EBI description of parent/child relationships](https://github.com/EBISPOT/OLS/blob/master/ols-web/src/main/asciidoc/generated-snippets/terms-example/links.adoc)
# "Hierarchical parents include is-a and other related parents, such as part-of/develops-from, that imply a hierarchical relationship"
url = 'http://www.ebi.ac.uk/ols/api/ontologies/fbcv/terms?size=500'
json_data = get_data(url)

# def find_parents():
iter_terms = _term_gen(json_data)
nodes = []
anc = []
roots = []
level = 0

for term in iter_terms:
    try:
        parent_url = term['_links']['hierarchicalParents']['href']
    except KeyError:  # there's no children for this one
        continue

    response = get_data(parent_url)

    # Generate the first run through of the table, which will include the parents of all the unique terms in the ont.

    for parent_term in response['_embedded']['terms']:
        nodes.append(term['obo_id'])
        anc.append(parent_term['obo_id'])
        roots.append(parent_term['is_root'])
            # yield term['obo_id'], parent_term['obo_id'], parent_term['is_root']

# combine into a dataframe; set ancestor level to 0
parents = pd.DataFrame([nodes, anc, roots, list(np.zeros(len(nodes)))], index = ['id', 'ancestor_id', 'is_root', 'ancestor_level']).T
# .set_index('id')

level += 1

ancestors = []


# TODO: log the baby value
# loop over ancestors
for index, row in parents.iterrows():
    if(index < 10):
        baby = row.id
        curr_ancestor = row.ancestor_id
        # get the parents of the current ancestor
        next_gen = parents[parents.id == curr_ancestor]
        # up the ancestor level
        next_gen.ancestor_level += 1
        # change the node id to be the original baby
        next_gen.loc[parents.id == curr_ancestor,"id"] = baby

        if(len(ancestors) == 0):
            ancestors = next_gen
        else:
            ancestors = pd.concat([ancestors, next_gen])

ancestors
