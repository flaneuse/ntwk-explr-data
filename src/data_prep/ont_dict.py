# @name:        ont_dict.py
# @title:       Creates an ontology dictionary for all terms in the NGLY1 graph network
# @description: Main outer file does the merge and checks for missing values.
#               [Data sources](https://github.com/flaneuse/ntwk-explr/blob/master/datain/DATA_README.md)
#               [Data pipeline](https://docs.google.com/presentation/d/1dk_1lTGAhB1tJZuUH9yfJoAZwznedHM_DHrCVFBqeW8/edit#slide=id.g3303550b82_0_110)
# @sources:     Ontology structures via OLS (GO, HP, MP, FBcv, FBbt, WormBase); gene annotations via mygene.info; NGLY1 network primarily Monarch
# @depends:     clean_neo4j.py, annot_GENE.py, ont_struct.py
# @author:      Laura Hughes
# @email:       lhughes@scripps.edu
# @date:        31 January 2018


# [0] Setup ----------------------------------------------------------------------
import numpy as np
import pandas as pd
import requests
import os
import warnings

# -- Atom notebook path settings --
# output_dir = 'dataout/'  # path within Atom notebook
# import src.data_prep.clean_neo4j as neo4j  # interface to query network
# import src.data_prep.annot_GENE as gene # interface to get gene annotations
# import src.data_prep.ont_struct as ont  # functions to pull ontology data


# -- commpand line prompt settings --
output_dir = '../../dataout/' # path from command line prompt
import clean_neo4j as neo4j # interface to query network
# import annot_GENE as gene # interface to get gene annotations
import ont_struct as ont # functions to pull ontology data


# [1] Pull unique nodes from Nuria's graph -----------------------------------------------------------------
# node_file = 'https://raw.githubusercontent.com/NuriaQueralt/ngly1/master/neo4j-community-3.0.3/import/ngly1/ngly1_concepts.tsv' # if want to pull directly from the input file to neo4j
nodes = neo4j.get_nodes()

# <<< pull_ontsource(id, sep = ':') >>>
# @name:        pull_ontsource
# @title:       grab node ID source type
# @description: used to merge ids to ontology hierarhical levels from OLS; see `check_ontid_unique.py`)
# @input:       *id* string, *sep*: separator between id source and source-specific id
# @output:      stub containing the ont source for that particular id
# @example:     pull_ontsource('ZFIN:ZDB-GENE-051023-7')
def pull_ontsource(id, sep = ':'):
    split_id = id.split(sep)
    if (len(split_id) > 1):
        return split_id[0]
    else:
        warnings.warn("Cannot find the source for the id. Need to change `sep`?")

# (TEST): make sure I'm pulling all the ID types
# nodes['ont_source'] = nodes.node_id.apply(pull_ontsource)
# nodes.groupby('node_type').ont_source.value_counts()

# <<< get_ontid(nodes, drop_source = True) >>>
# @name:        get_ontid
# @title:       map node ID type to ont_id from OLS
# @description: used to merge ids to ontology hierarhical levels; see `check_ontid_unique.py`)
#        NOTE: GENE merging taken care of by merging to annotations (translated via mygene.info) (NCBIGene, ZFIN, MGI, RGD, WormBase, Xenbase, FlyBase, UniProt, InterPro)
#        NOTE: ignoring PHYS, GENO, VARI for now (PHYS requires too much work for the moment; GENO/VARI are low numbers and would require translating to genes then merging -- if that's even appropriate to lump mutation w/ original function)
#        Also ignoring, for now:
#        ANAT      CL (only 7; not in UBERON)
#        DISO      ZP (271; not in OLS); disease DB: DOID (17), OMIM (6), MESH (4)
#        TODO: revisit DISO when phenotypes/diseases are better delineated
#        TODO: revisit GENE when genes/proteins are better delineated
# @input:       *nodes*: dataframe containing node_id, *drop_source*: binary option to drop column containing the node ont_source
# @output:      *nodes* dataframe
# @example:     get_ontid(nodes)
def get_ontid(nodes, drop_source = True):
    # ont_source (neo4j graph): ont_id (OLS ID)
    id2ontid = {
        # ANAT
        'UBERON':   'UBERON',
        # CHEM
        'CHEBI':    'CHEBI',
        # DISO
        'MP': 'mp',
        'FBbt': 'FBbt',
        'HP': 'hp',
        'WBPhenotype': 'wbphenotype',
        'FBcv': 'FBcv'
    }

    nodes['ont_source'] = nodes.node_id.apply(pull_ontsource)
    nodes['ont_id'] = nodes['ont_source'].map(id2ontid)

    if (drop_source):
        return nodes.drop('ont_source', axis = 1)
    else:
        return nodes

nodes = get_ontid(nodes)

# [2] Pull gene annotations -----------------------------------------------------------------
# 2 purposes:   1) translate node_id (for genes) to standarized NCBI Entrez gene names
#               2) for each gene, pull associated gene ontology (GO) terms

# [3] Create ontology hierarchical levels for *all* possible terms in base ontologies -----------------------------------------------------------------
# Get ontology structures + hierarchy for all ontologies
# OLS ids
ont_ids = {
    'ANAT': ['UBERON'],
    'CHEM': ['CHEBI'],
    'DISO': ['FBcv', 'wbphenotype', 'FBbt', 'mp', 'hp'],
    'GENE': ['go']
}


def create_ont_dict(ont_ids, output_dir, merge=False):
    files = sorted(os.listdir(output_dir))

    # little helper to see if file has already been generated.
    def check_exists(files, ont_id, file_type):
        file_name = [file_name for idx, file_name in enumerate(
            files) if ont_id + '_' + file_type in file_name]
        if(len(file_name) == 1):
            return file_name[0]
        elif (len(file_name) > 1):
            return file_name[-1]
        else:
            return False

    # create placeholder for term dictionaries
    ont_terms = []

    # create placeholder for term parents
    parents = {}

    # create placeholder for term ancestors
    ancestors = []

    for ont_type, ont_ids in ont_ids.items():
        print('\n\n---' + ont_type + '---')
        for ont_id in ont_ids:
            print('\n*' + ont_id + '*')

            # -- terms --
            term_file = check_exists(files, ont_id, 'terms')
            if(term_file):
                # file already exists; read it in
                print('reading in term file')
                ont_term = pd.read_csv(output_dir + term_file, sep = '\t')
            else:
                # create file
                print('creating term file')
                ont_term = ont.get_terms(ont_id, save_terms=True, output_dir=output_dir)
            # either way, append info for merging w/ nodes.
            ont_term['ont_id'] = ont_id
            ont_term['node_type'] = ont_type
            ont_terms.append(ont_term)

            # -- parents --
            parent_file = check_exists(files, ont_id, 'parents')
            if(parent_file):
                # file already exists; read it in
                print('reading in parents file')
                parents[ont_id] = pd.read_csv(output_dir + parent_file, sep='\t', index_col=0)
            else:
                # create file
                print('creating parents file')
                parents[ont_id] = ont.find_parents(ont_terms[ont_id], ont_id, save_terms=True, output_dir=output_dir)

            # -- ancestors --
            hierarchy_file = check_exists(files, ont_id, 'ancestors')
            if(hierarchy_file):
                if (hierarchy_file.find('TEMP') > -1):
                    start_idx = int(hierarchy_file.split('TEMPidx')[1].replace('.tsv', ''))
                    # file already exists but is incomplete; read it in
                    print('reading in partial ancestor hierarchical structure file')
                    ancestor_partial = pd.read_csv(output_dir + hierarchy_file, sep='\t', index_col=0)
                    print('creating the rest of the ancestor hierarchical structures, starting at index ' + str(start_idx))
                    ancestor = ont.find_ancestors(
                        parents[ont_id], ont_id=ont_id, save_terms=True, output_dir=output_dir, start_idx = start_idx)
                    # combine the two halves
                    ancestor = pd.concat([ancestor, ancestor_partial], ignore_index=True)
                    ancestor.to_csv(output_dir + str(pd.Timestamp.today().strftime('%F')) + '_' + ont_id + '_ancestors_all.tsv', sep='\t')
                else:
                    # file already exists; read it in
                    print('reading in ancestor hierarchical structure file')
                    ancestor = pd.read_csv(output_dir + hierarchy_file, sep='\t', index_col=0)
            else:
                # create file
                print('creating hierarchical structure file')
                ancestor = ont.find_ancestors(
                    parents[ont_id], ont_id=ont_id, save_terms=True, output_dir=output_dir)
            # either way, append info for merging w/ nodes.
            ancestor['ont_id'] = ont_id
            ancestor['node_type'] = ont_type
            ancestors.append(ancestor)



    ont_terms = pd.concat(ont_terms, ignore_index=True)
    # append the roots before converting to DataFrame
    roots = get_root_ancestors(ont_terms)
    ancestors.append(roots)
    ancestors = pd.concat(ancestors, ignore_index=True)

    if(merge):
        # merge together ontology terms + hierarhical levels
        merged = pd.merge(ont_terms, ancestors, on=["node_type", "ont_id", "id"], how="outer", indicator=True)
        checked = check_merge(merged)

        if(checked):
            warnings.warn('Merge problems found')

        merged.to_csv(
            output_dir + str(pd.Timestamp.today().strftime('%F')) + '_ont_dict.tsv', sep='\t')
        return merged
    else:
        return {'parents': parents, 'ont_terms': ont_terms, 'ont_hierarchy': ancestors}

# TODO: incorporate this into the ancestor code
def get_root_ancestors(ont_terms):
    roots = ont_terms[ont_terms.is_root]
    roots = roots[['node_type', 'ont_id','id']]
    roots['node_level'] = 0
    roots['ancestors'] = np.NaN
    return roots

def check_merge(merged):
    no_hierarchy = []
    no_base = []

    print('{0:.1f}%  successfully merged'.format(
        (sum(merged._merge == 'both') / len(merged)) * 100))

    left_only = merged._merge == 'left_only'
    right_only = merged._merge == 'right_only'

    if(sum(left_only)):
        print(str(sum(left_only)) + ' lacking ontology hierarchy')
        no_hierarchy = merged[left_only]

    if(sum(right_only)):
        print(str(sum(right_only)) + ' lacking base terms')
        no_base=merged[right_only]

    if(sum(left_only) | sum(right_only)):
        if(sum(left_only)):
            print('\n*missing hierarchy terms*\n')
            left_bytype = merged[left_only].groupby('node_type').ont_id.value_counts()
            print(left_bytype)
        if(sum(right_only)):
            print('\n*missing base terms*\n')
            right_bytype = merged[right_only].groupby('node_type').ont_id.value_counts()
            print(right_bytype)
        return {'no hierarhy terms': no_hierarchy, 'no base terms': no_base}
    else:
        return


# call to create the dictionary
onts = create_ont_dict(ont_ids, output_dir, merge=True)

onts.head()
# [4] Merge together nodes in network, annotations, and ontology levels -----------------------------------------------------------------
# -- Merge nodes + annotations --
# GO_terms = gene.go['annots']
# nodes.head()
# def merge_nodes_annots(nodes, GO_terms):
# GO_terms = GO_terms[['gene_name', 'id', ]]
#
# pd.merge(nodes, GO_terms, left_on=["node_type", "ont_id", "id"], how="outer", indicator=True)
#
# merge_nodes_annots(nodes, gene.go['annots']
# GO_terms.head()
