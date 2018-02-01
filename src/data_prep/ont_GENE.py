# Pulls ontology tree from EBI's Ontology Lookup Service (OLS) API (https://www.ebi.ac.uk/ols/index);
# then parses into individual terms and creates the parents for each individual term.
# Laura Hughes, lhughes@scripps.edu, 31 January 2018
# Building in part off of python [ols-client library](https://github.com/cthoyt/ols-client/blob/master/src/ols_client/client.py)

# Setup
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
        print('calling API')
        json_data = get_data(next_page)
        next_page = addit_pages(json_data) # update next page

        terms = pd.concat([terms,pull_terms(json_data)])

    parents = None

    # return { 'terms': terms, 'parents': parents }
    return terms

t = get_terms('fbcv')

# [EBI description of parent/child relationships](https://github.com/EBISPOT/OLS/blob/master/ols-web/src/main/asciidoc/generated-snippets/terms-example/links.adoc)
# "Hierarchical parents include is-a and other related parents, such as part-of/develops-from, that imply a hierarchical relationship"

def find_parents():
    iter_terms = _term_gen(json_data)

    for term in iter_terms:
        try:
            parent_url = term['_links']['hierarchicalParents']['href']
        except KeyError:  # there's no children for this one
            continue

        response = get_data(parent_url)

        for parent_term in response['_embedded']['terms']:
            yield term['obo_id'], term['label'], parent_term['obo_id'], parent_term['label']

for child in find_parents():
    # print(parent)
    print(child)
