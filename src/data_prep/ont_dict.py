# @name: ont_dict.py
# @title: Creates an ontology dictionary for all terms in the NGLY1 matrix
# @description:  Main outer file does the merge and checks for missing values.
#                [Data sources](https://github.com/flaneuse/ntwk-explr/blob/master/datain/DATA_README.md)
#                [Data pipeline](https://docs.google.com/presentation/d/1dk_1lTGAhB1tJZuUH9yfJoAZwznedHM_DHrCVFBqeW8/edit#slide=id.g3303550b82_0_110)
# @NOTE: should not be run on ethernet; OLS refuses connection
# @author: Laura Hughes
# @email: lhughes@scripps.edu
# @date: 31 January 2018


# [0] Setup ----------------------------------------------------------------------
# output_dir = 'dataout/'  # path within Atom notebook
output_dir = '../../dataout/' # path from command line prompt

import pandas as pd
import requests
import os
import warnings

# interface to query network
# from src.data_prep.clean_neo4j import get_nodes  # path within Atom notebook
from clean_neo4j import get_nodes # path from command line prompt

# functions to pull ontology data
# import src.data_prep.ont_struct as ont  # path within Atom notebook
import ont_struct as ont # path from command line prompt


# Pull unique nodes from Nuria's graph
# node_file = 'https://raw.githubusercontent.com/NuriaQueralt/ngly1/master/neo4j-community-3.0.3/import/ngly1/ngly1_concepts.tsv'
nodes = get_nodes()

nodes.head()
nodes['type'] = nodes.node_id.apply(lambda x: x[0:2])
# # -- Pull gene annotations --
# # genes
# import src.data_prep.annot_GENE as gene

# -- Get ontology structures + hierarchy for all ontologies. --
# OLS ids
ont_ids = {
    'DISO': ['FBcv', 'wbphenotype', 'FBbt', 'mp', 'hp'],
    'GENE': ['go'],
    'ANAT': ['UBERON'],
    'CHEM': ['CHEBI']
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
    ont_dicts = {}

    # create placeholder for term parents
    parents = {}

    # create placeholder for term ancestors
    ancestors = {}

    for ont_type, ont_ids in ont_ids.items():
        print('\n\n---' + ont_type + '---')
        for ont_id in ont_ids:
            print('\n*' + ont_id + '*')

            # -- terms --
            term_file = check_exists(files, ont_id, 'terms')
            if(term_file):
                # file already exists; read it in
                print('reading in term file')
                ont_dicts[ont_id] = pd.read_csv(
                    output_dir + term_file, sep='\t', index_col='id')
            else:
                # create file
                print('creating term file')
                ont_dicts[ont_id] = ont.get_terms(
                    ont_id, save_terms=True, output_dir=output_dir)

            # -- parents --
            parent_file = check_exists(files, ont_id, 'parents')
            if(parent_file):
                # file already exists; read it in
                print('reading in parents file')
                parents[ont_id] = pd.read_csv(
                    output_dir + parent_file, sep='\t')
            else:
                # create file
                print('creating parents file')
                parents[ont_id] = ont.find_parents(
                    ont_dicts[ont_id], ont_id, save_terms=True, output_dir=output_dir)

            # -- ancestors --
            hierarchy_file = check_exists(files, ont_id, 'ancestors')
            if(hierarchy_file):
                # file already exists; read it in
                print('reading in ancestor hierarchical structure file')
                ancestors[ont_id] = pd.read_csv(
                    output_dir + hierarchy_file, sep='\t')
            else:
                # create file
                print('creating hierarchical structure file')
                ancestors[ont_id] = ont.find_ancestors(
                    parents[ont_id], ont_id=ont_id, save_terms=True, output_dir=output_dir)

    if(merge):
        # two stages: for genes, merge gene to annotations

        # unnest names and

        # merge together ontology terms + hierarhical levels
        merged = pd.merge(ont_dicts, ancestors, on="id",
                          how="outer", indicator=True)
        checked = check_merge(merged)

        if(checked):
            warnings.Warning('Merge problems found')

        merged.to_csv(
            output_dir + str(pd.Timestamp.today().strftime('%F')) + '_ont_dict.tsv', sep='\t')
        return merged
    else:
        return {'parents': parents, 'ont_terms': ont_dicts, 'ont_hierarchy': ancestors}


def check_merge(merged):
    no_ont = []
    no_base = []

    print('{0}%\n successfully merged'.format(
        sum(merged._merge == 'both') / len(merged)))

    left_only = merged._merge == 'left_only'
    right_only = merged._merge == 'right_only'

    if(sum(left_only)):
        print(str(sum(left_only)) + ' lacking ontology hierarchy')
        no_ont = merged[left_only]

    if(sum(right_only)):
        print(str(sum(right_only)) + ' lacking base terms')
        no_base = merged[right_only]
    if(left_only | right_only):
        return {'no ontology terms': no_ont, 'no base terms': no_base}
    else:
        return


onts = create_ont_dict(ont_ids, output_dir)


# Create a master template for all the different ontology types

# -- Merge --
#
# # # genes
# import src.data_prep.annot_GENE as gene
#
# genes = data['NFE2L1:ENGASE']['nodes']
#
# onts = pd.merge(genes, gene.gene_annot, left_on="node_id", right_on="id", how="left", indicator=True)
# onts.head()
# # check if any vars are unmerged.
# onts._merge.value_counts()
#
#
# left join to nodes
onts = pd.merge(genes, gene.gene_annot, on="id", how="left", indicator=True)
onts.head()
# check if any vars are unmerged.
onts._merge.value_counts()

# find missing terms; spot-check if there's any patterns.
missing = onts[onts._merge == 'left_only'][[
    'id', 'node_name']].sort_values(['id'])
print(missing)

# Count frequency of GO terms
onts.go_id.value_counts()

# Count number of GO terms per ID.
onts.groupby('id')['go_id'].count().describe()
