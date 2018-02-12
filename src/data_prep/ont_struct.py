# @name: ont_struct.py
# @title: Imports ontology tree and calculates hierarchical level per ontology term
# @description:  Pulls ontology tree from EBI's Ontology Lookup Service (OLS) API (https://www.ebi.ac.uk/ols/index);
#               then parses into individual terms and creates the parents for each individual term.
#               Building in part off of python [ols-client library](https://github.com/cthoyt/ols-client/blob/master/src/ols_client/client.py)
# @author: Laura Hughes
# @email: lhughes@scripps.edu
# @date: 31 January 2018

# Setup
import numpy as np
import pandas as pd
import requests
import progressbar
import time

# After looking through the documentation and all the associated fields that come out from the API call, it looks like there's no way to avoid
# doing a loop through the entire tree, starting from end node and iterating till you hit the root (s).
# Perhaps not the fastest way, but the most direct way will start from the end node rather than going from the roots down.

# NOTE: Would be faster to pull all the terms from a static .owl file to find the parents and then use these same functions to assemble the hierarchy.
# However, that introduces more dependencies, and OLS has already gone through the bother of standardizing the output files.
# So, the slow but steady way...

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
#     @example: get_data('http://www.ebi.ac.uk/ols/api/ontologies/go/terms?size=500')
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
                    print('index: ' + str(idx) + ' (counter: ' + str(counter) + ')')
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

def find_nextgen(parent_df, original_id, child_id,  level = -1, ancestors = [], levels = []):
# def find_nextgen(parent_df, original_id, child_id, level = -1, ancestors = pd.DataFrame()):
    # find the id(s) of the parent of child_id
    # need to create a copy so it's not assigning a value to a view on the data.
    next_gen = parent_df.copy()[parent_df.id == child_id]

    # decrease the ancestor level
    next_gen.ancestor_level = level
    # counter on recursion level
    level -= 1

    # change the node id to be the original baby id
    next_gen.loc[:,"id"] = original_id

    for idx, row in next_gen.iterrows():
        to_add = pd.DataFrame(row).T
        ancestors
        # ancestors = pd.concat([ancestors, to_add], ignore_index=True)
        if (not row.is_root):
            find_nextgen(parent_df, original_id, row.ancestor_id, level, ancestors)
        else:
            print(ancestors)
            return ancestors
    return None

original_id = 'CHEBI:64709'
child_id = 'CHEBI:23367'
child_id = ['CHEBI:24431', 'FBcv:00000525']

output = pd.DataFrame()

def find_parent(parent_df, original_id, child_id, level = -1, ancestors = pd.DataFrame()):
    global output
    # print("------- LEVEL " + str(level) + " ------- ")
    print('outer call')
    print(id(output))
    if (level == -1):
        # initialize ancestors with the root node.
        ancestors = pd.DataFrame([{'is_root': False, 'id': original_id, 'parent_id': original_id, 'level': 0}])

    # empty holder for the current ancestor of child_id
    ancestor = pd.DataFrame()

    # resets level indices so 0 is the root nodes
    def reset_level(output):
        root_level = min(output.level)
        output['new_level'] = output.level - root_level
        return output


    # find the row(s) that contain the parent id for the current child_id
    if(type(child_id) == str):
        parent_row = parent_df[parent_df.id == child_id]
    elif((isinstance(child_id, pd.Series)) | (type(child_id) == list)):
        parent_row = parent_df[parent_df.id.isin(child_id)]
    else:
        print('Error: weird child_id supplied')
        return

    # remove duplicates if there are any
    parent_row = parent_row.drop('id', axis = 1).drop_duplicates()
    # pull parent id;
    ancestor['parent_id'] = parent_row.ancestor_id
    # pull if it's a root
    ancestor['is_root'] = parent_row.is_root
    # save the lowest level, which doesn't change throughout the recursion
    ancestor['id'] = original_id

    # set the level
    ancestor['level'] = level

    # print('ancestor')
    # print(ancestor)

    # -- recurse --
    if(parent_row.is_root.all()):
        print('ALL')
        # have hit the root node for all the branches
        # combine together all the stuff from before
        ancestors = pd.concat([ancestor, ancestors], ignore_index=True)

        # concat any previous results to the re-leveled ancestors
        ancestors = reset_level(ancestors)
        # print('ancestors (root)')
        # print(ancestors)
        output = pd.concat([output, ancestors], ignore_index=True)
        print(id(output))
        return output.sort_values('new_level')
    elif(len(parent_row) > 1):
        if(parent_row.is_root.any()):
            print('[ANY]')
            # hit a root on one of the paths.
            # make a copy of the exisiting ancestors up to this point
            root_children = pd.concat([ancestor[(ancestor.is_root)], ancestors], ignore_index=True)
            # root_children = ancestors[(ancestors.is_root) | (ancestors.level > level)]

            # reset index on the root one
            root_children = reset_level(root_children)

            # print('rebase: root children')
            # print(root_children)

            # append the root + children to the output
            output = pd.concat([output, root_children], ignore_index=True)
            print(id(output))
            # pop off the root
            # ancestors = ancestors[ancestors.is_root == False]
        # print('[BRANCH]')
        branches = ancestor[(ancestor.is_root == False)]
        last_idx = branches.index[-1]
        for idx, row in branches.iterrows():
            # print('branch ' + str(loop_ctr) + "***********************************")
            # loop_ctr += 1
            to_add = pd.DataFrame(row).T
            ancestors = pd.concat([to_add, ancestors], ignore_index=True)
            if idx == last_idx:
                # exit the loop
                # print('********** exiting loop ********** ')
                return find_parent(parent_df, original_id, row.parent_id, level - 1, ancestors)
            else:
                find_parent(parent_df, original_id, row.parent_id, level - 1, ancestors)
        # print('ancestors -- after appending output')
        # print(ancestors)
        # continue onward with the remaining items
        #    call with the parent as the child
        #    drop down a level

    else:
        # print('continue')
        # combine together all the stuff from before
        ancestors = pd.concat([ancestor, ancestors], ignore_index=True)
        # print('ancestors (continue)')
        # print(ancestors)
        # continue onward with all the items
        #    call with the parent as the child
        #    drop down a level
        return find_parent(parent_df, original_id, parent_row.ancestor_id, level - 1, ancestors)


def find_nextgen(parent_df, original_id, child_id,  level = -1, ancestors = [], levels = []):
    # find the id(s) of the parent of child_id
    # need to create a copy so it's not assigning a value to a view on the data.
    next_gen = parent_df.copy()[parent_df.id == child_id]
    parent_id = list(next_gen.ancestor_id)

    # decrease the ancestor level
    next_gen.ancestor_level = level
    # counter on recursion level
    level -= 1

    # change the node id to be the original baby id
    next_gen.loc[:,"id"] = original_id


    for idx, row in next_gen.iterrows():
        print('--> starting loop')
        print(idx)
        # to_add = pd.DataFrame(row).T
        # print('parent: ' + row.ancestor_id)
        ancestors.append(row.ancestor_id)
        levels.append(level)
        # to_add = pd.DataFrame({'parent': [row.ancestor_id], 'root': [row.is_root], 'id': [row.id]})
        # check if row already exists (and ancestors is initialized)
        # if ((len(ancestors) == 0) | (not (ancestors == to_add).all(1).any())):
        # ancestors = pd.concat([ancestors, to_add], ignore_index=True)
        # print(ancestors)
        if (not row.is_root):
            find_nextgen(parent_df, original_id, row.ancestor_id, level, ancestors)
            # return ancestors
        else:
        # #     print('found root')
        # #     # print(ancestors)
            return ancestors
    return {'ancestors': ancestors, 'levels': levels}

# QA-QC: spot check a few paths within fbcv ontology
# fbcv = get_terms('fbcv')
# fbcv = pd.read_csv('dataout/2018-02-09FBcv_terms.tsv', sep = '\t')
# # parent_df = find_parents(fbcv, 'fbcv', save_terms = False)
# parent_df = pd.read_csv('dataout/2018-02-09_FBcv_parents.tsv', sep = '\t')
# ids = parent_df.id.sample(5)
# for term in ids:
#     print(term)
#     find_parent(parent_df, term, term)
# weirdos = x.parent_id[x.new_level == 1]
#
#
# parent_df[parent_df.id.isin(weirdos)].sort_values(['is_root', 'ancestor_id'])
# id(ids)
# id(parent_df)
# y = parent_df.copy()
# id(y)
# ids.index[-1]
#
# # symmetric; works fine
# find_nextgen(parent_df, parent_df.id[424], parent_df.id[424])
# # symmetric but nested; fine.
# find_parent(parent_df, 'CHEBI:64709', 'CHEBI:64709')
#
# # asymmetric; problematic
# # ISSUE: output not global; points to different things within loop and therefore doesn't save stuff.
# x = find_parent(parent_df, parent_df.id[817],parent_df.id[817])
# x = find_nextgen(parent_df, parent_df.id[817],parent_df.id[817])
# pd.DataFrame(x)
# x.sort_index()
# x.drop(['level'], axis = 1).drop_duplicates().sort_values('new_level')
# x.drop(['level'], axis = 1).drop_duplicates().new_level.value_counts().sort_index()
#
# x.drop(['level'], axis = 1).shape
# x.sort_values(['parent_id', 'new_level', 'level'])
