# @name: ont_struct.py
# @title: Imports ontology tree and calculates hierarchical level per ontology term
# @description:  Pulls ontology tree from EBI's Ontology Lookup Service (OLS) API (https://www.ebi.ac.uk/ols/index);
#               then parses into individual terms and creates the parents for each individual term.
#               Building in part off of python [ols-client library](https://github.com/cthoyt/ols-client/blob/master/src/ols_client/client.py)
# @author: Laura Hughes
# @email: lhughes@scripps.edu
# @date: 31 January 2018

# After looking through the documentation and all the associated fields that come out from the API call, it looks like there's no way to avoid
# doing a loop through the entire tree, starting from end node and iterating till you hit the root (s).
# Perhaps not the fastest way, but the most direct way will start from the end node rather than going from the roots down.

# NOTE: Would be faster to pull all the terms from a static .owl file to find the parents and then use these same functions to assemble the hierarchy.
# However, that introduces more dependencies, and OLS has already gone through the bother of standardizing the output files.
# So, the slow but steady way...

# [0] Setup ---------------------------------------------------------------------------------
import numpy as np
import pandas as pd
import requests
import progressbar
import time

# <<< get_data(url) >>>
# @name: get_data(url)
# @title: Access data from EBI API
# @description: returns json object with unfiltered layers of gooiness.
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
# @input: url from any API
# @output: False if query failed; json-ized data if successful
# @example: get_data('http://www.ebi.ac.uk/ols/api/ontologies/go/terms?size=500')
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
        return {'next': next_page, 'current': curr_page, 'last': last_page}
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
# returns a dataframe containing their ids, labels (names), descriptions, synonyms, iri (purl to ontobee), whether is a root node, and the url to call to get their hierarchicalParents
# [EBI description of parent/child relationships](https://github.com/EBISPOT/OLS/blob/master/ols-web/src/main/asciidoc/generated-snippets/terms-example/links.adoc)
# "Hierarchical parents include is-a and other related parents, such as part-of/develops-from, that imply a hierarchical relationship"
def pull_terms(json_data, filter_obs = True):
    iter_terms = _term_gen(json_data)

    ids = []
    labels = []
    descrips = []
    syn = []
    iri = []
    root = []
    parents = []


    # pull out the relevant values
    for term in iter_terms:
        # filter out the obsolete terms, if specified
        # removes:
        #   obsolete terms
        #   "Thing"
        if((not filter_obs) | ((not term['is_obsolete']) & pd.notnull(term['obo_id']))):
            ids.append(term['obo_id'])
            labels.append(term['label'])
            iri.append(term['iri'])
            root.append(term['is_root'])
            try:
                descrips.append(term['description'][0])
            except:
                descrips.append('')
            try:
                syn.append(term['synonyms'][0])
            except:
                syn.append('')
            try:
                parents.append(term['_links']['hierarchicalParents']['href'])
            except KeyError:  # there's no parents for this one
                parents.append('')
                continue
    # convert to a dataframe
    terms = pd.DataFrame([ids, labels, descrips, syn, iri, root, parents], index = ['id', 'label', 'description', 'synonyms', 'node_url', 'is_root', 'parent_url']).T.set_index('id')

    return terms

# Primary API call to OLS to get the unique terms.
# returns terms, parents
# --> term dictionary
# @example: fbcv = get_terms('fbcv')
def get_terms(ont_id, base_url = 'http://www.ebi.ac.uk/ols/api/ontologies/', end_url = '/terms?size=500', save_terms = False, output_dir = ''):
    url = base_url + ont_id + end_url

    json_data = get_data(url)

    # set up containers for loops
    terms = pull_terms(json_data)
    next_page = addit_pages(json_data)

    with progressbar.ProgressBar(max_value = next_page['last']) as bar:
        while(next_page):
            bar.update(next_page['current'])
            json_data = get_data(next_page['next'])
            next_page = addit_pages(json_data) # update next page

            terms = pd.concat([terms,pull_terms(json_data)])

    if (save_terms):
        terms.to_csv(output_dir + str(pd.Timestamp.today().strftime('%F')) + '_' + ont_id + '_terms.tsv', sep='\t')

    return terms

# @description: pulls out all the immediate hierahrichal parents for a
#               [EBI description of parent/child relationships](https://github.com/EBISPOT/OLS/blob/master/ols-web/src/main/asciidoc/generated-snippets/terms-example/links.adoc)
#               "Hierarchical parents include is-a and other related parents, such as part-of/develops-from, that imply a hierarchical relationship"
# @input:       *terms*: dataframe of terms, output of `get_terms`
#
# @example:     parent_df = find_parents(fbcv, ont_id = 'fbcv')
def find_parents(terms, ont_id, save_terms = True, output_dir = ''):
    nodes = []
    anc = []
    roots = []
    counter = 0

    with progressbar.ProgressBar(max_value = len(terms), initial_value=0) as bar:
        for idx, row in terms.iterrows():
        # try:
        #     parent_url = term['_links']['hierarchicalParents']['href']
        # except KeyError:  # there's no children for this one
        #     continue
            if((row.parent_url != "") & (pd.notnull(row.parent_url))):
                try:
                    response = get_data(row.parent_url)
                except:
                    print('\n index: ' + str(idx) + ' (counter: ' + str(counter) + ')')
                    print('server overloaded; waiting 2 min. and caching results')
                    temp = pd.DataFrame([nodes, anc, roots], index = ['id', 'ancestor_id', 'is_root']).T
                    temp.to_csv(output_dir + str(pd.Timestamp.today().strftime('%F')) + '_' + ont_id + '_parents_TEMPidx' + str(counter) + '.tsv', sep='\t')
                    time.sleep(120)
                    response = get_data(row.parent_url)

                for parent_term in response['_embedded']['terms']:
                    nodes.append(idx)
                    anc.append(parent_term['obo_id'])
                    roots.append(parent_term['is_root'])
                        # yield term['obo_id'], parent_term['obo_id'], parent_term['is_root']
            counter += 1
            if (counter % 5 == 0):
                bar.update(counter)

    # combine into a dataframe; set ancestor level to 0
    parents = pd.DataFrame([nodes, anc, roots], index = ['id', 'ancestor_id', 'is_root']).T

    if (save_terms):
        parents.to_csv(output_dir + str(pd.Timestamp.today().strftime('%F')) + '_' + ont_id + '_parents.tsv', sep='\t')

    return parents

# <<< find_nextgen() >>>
# @name:
# @title:
# @description:
# @NOTE: lots of permutations of this funciton were written. One of the main sticking points was
# whether to concat a DataFrame in each iteration of the loop, or whether to save each variable in
# a separate list. While both work (or should, in principle), using a DataFrame means that the output
# variable needs to be declared as a global, or else during the recursion results will be saved over/lost.
# For simplicity, then, passing everything as lists and converting later.
# @input:
# @output:
# @example:
# outer function to pull an ancestor for a specific ID
def find_ancestors_1node(parent_df, id, reverse = True, return_paths = False):
    root_ids = set(parent_df.ancestor_id[parent_df.is_root == True])

# << find_nextgen() >> # helper function to recurse through the parent ids and ID all the ancestors.
# variation on https://www.python.org/doc/essays/graphs/
    def find_nextgen(parent_df, child_id, root_ids, path = [], paths = []):
        # update the path with the current search param
        # path will reset after every loop
        path = path + [child_id]

        if(child_id in root_ids):
            # have hit the root node
            paths.append(path)
            return path

        # find the id(s) of the parent of child_id
        parent_row = parent_df[parent_df.id == child_id]

                # -- recurse --
        for idx, row in parent_row.iterrows():
            find_nextgen(parent_df, row.ancestor_id, root_ids, path, paths)
        return paths

    # << reset_level(paths, reverse) >> : helper function to standardize indices
    # resets level indices so 0 is the root nodes
    def reset_level(paths, reverse):
        path_dict = {}
        for idx, path in enumerate(paths):
            # reverse the list, so the root is at 0
            if(reverse):
                path.reverse()
            for ont_idx, ont_id in enumerate(path):
                # update dictionary
                if ont_idx in path_dict:
                    # dictionary already has that value; append if it doesn't already exist within list
                    if ont_id not in path_dict[ont_idx]:
                        path_dict[ont_idx].append(ont_id)
                else:
                    path_dict[ont_idx] = [ont_id]
        return path_dict

    # Calculate path
    paths = find_nextgen(parent_df, id, root_ids)
    ont_idx = reset_level(paths, reverse)

    if (return_paths):
        return {'paths': paths, 'ont_idx': ont_idx}
    else:
        return ont_idx

# @NOTE:    certain high level nodes have an NA id. These were filtered out upstream.
#           As a result, any descendants of this node will have NA ancestors; assuming these ont terms aren't particularly impt.
#           Return value for ancestors will be NA
def find_ancestors(parent_df, ont_id = '', save_terms = True, output_dir = '', ids = [], reverse = True, return_paths = False, save_freq = 2500):
    # container for output
    output = pd.DataFrame()

    # ids is an optional testing parameter; if not declared, will look for all the ids.
    # Remove duplicate ids; some ids have multiple parents, therefore need to keep in parent_df.
    # However, including them the entire time will add unnecessary calculations of the same paths.
    if(len(ids) == 0):
        ids = pd.unique(parent_df.id)
    elif(isinstance(ids, pd.Series)):
        # convert series to Numpy ndarray
        ids = ids.as_matrix()

    with progressbar.ProgressBar(max_value = len(ids)) as bar:
        for idx, node_id in np.ndenumerate(ids):
            ancestors = find_ancestors_1node(parent_df, id = node_id, reverse = reverse, return_paths = return_paths)

            # make sure ancestors returned something. If an ancestor has no unique ID, it was filtered out; return NA
            if(return_paths):
                if(len(ancestors['ont_idx']) > 0):
                    output = pd.concat([output, pd.DataFrame({'id': node_id, 'ancestors': [ancestors['ont_idx']], 'paths': [ancestors['paths']], 'node_level': max(ancestors['ont_idx'].keys())})], ignore_index=True)
                else:
                    output = pd.concat([output, pd.DataFrame({'id': node_id, 'ancestors': [np.NaN], 'paths': [np.NaN], 'node_level': [np.NaN]})], ignore_index=True)
            else:
                if(len(ancestors) > 0):
                    output = pd.concat([output, pd.DataFrame({'id': node_id, 'ancestors': [ancestors], 'node_level': max(ancestors.keys())})], ignore_index=True)
                else:
                    output = pd.concat([output, pd.DataFrame({'id': node_id, 'ancestors': [np.NaN], 'node_level': [np.NaN]})], ignore_index=True)

            if (idx[0] % 10 == 0):
                bar.update(idx[0])

            if (idx[0] % save_freq == 0):
                output.to_csv(output_dir + str(pd.Timestamp.today().strftime('%F')) + '_' + ont_id + '_ancestors' + '_TEMPidx' + str(idx[0]) + '.tsv', sep='\t')

    if (save_terms):
        output.to_csv(output_dir + str(pd.Timestamp.today().strftime('%F')) + '_' + ont_id + '_ancestors.tsv', sep='\t')

    return output


# QA-QC: spot check a few paths within fbcv ontology
# fbcv = get_terms('fbcv') # call to API; requires ~ 7-10 min.
# fbcv = pd.read_csv('dataout/2018-02-09_FBcv_terms.tsv', sep = '\t')
# # parent_df = find_parents(fbcv, 'fbcv', save_terms = False) # call to API; requires 20-30 min.
# parent_df = pd.read_csv('dataout/2018-02-12_FBcv_parents.tsv', sep = '\t')
#
#
# # Initial tests; used in the development of the scripts
# # symmetric; works fine ['FBcv:0003163']
# find_ancestors_1node(parent_df, parent_df.id[424])
#
# # symmetric but nested; fine.
# find_ancestors_1node(parent_df, 'CHEBI:64709')
#
# # asymmetric; problematic ['GO:0009953']
# # initial issues: output not global; points to different things within loop and therefore doesn't save stuff.
# find_ancestors_1node(parent_df, parent_df.id[817])
#
# # Random sampling testing; checked by eye to make sure okay.
# ids = parent_df.id.sample(5)
# find_ancestors(parent_df, ids = ids, return_paths = True, save_terms = False)



# testers when the return object was a long data frame.
# ont_dicts.sort_index()
# ont_dicts.drop(['level'], axis = 1).drop_duplicates().sort_values('new_level')
# ont_dicts.drop(['level'], axis = 1).drop_duplicates().new_level.value_counts().sort_index()
#
# ont_dicts.drop(['level'], axis = 1).shape
# ont_dicts.sort_values(['parent_id', 'new_level', 'level'])
