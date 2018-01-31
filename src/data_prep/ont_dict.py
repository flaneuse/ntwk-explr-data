# ont_dict.py
# Creates an ontology dictionary for all terms in the NGLY1 matrix
# Laura Hughes, lhughes@scripps.edu, 29 January 2018
#
# Data sources: https://github.com/flaneuse/ntwk-explr/blob/master/datain/DATA_README.md

# Main outer file does the merge and checks for missing values.

import pandas as pd


import pronto
from lxml import objectify



path = '/Users/laurahughes/GitHub/ntwk-explr/datain/ontology/DISO_upheno_mp.owl'
ont = pronto.Ontology(path)
print(ont.obo)
print(ont.json)

for term in ont:
    if term.parents:
        print(term.parents)

parsed = objectify.parse(open(path))

# Pull unique nodes from Nuria's graph
node_file = 'https://raw.githubusercontent.com/NuriaQueralt/ngly1/master/neo4j-community-3.0.3/import/ngly1/ngly1_concepts.tsv'
nodes = pd.read_csv(node_file)

nodes.head()

nodes.rename(columns = {'id:ID': 'id', ':LABEL': 'node_type', 'preflabel': 'node_name', 'synonyms:IGNORE': 'name_syn', 'description': 'node_descrip'}, inplace=True)

genes = nodes[nodes['node_type'] == 'GENE'][['id', 'node_name']]

genes.head()
# Check that nodes are unique
# Rename vars
# Remove unnecessary columns

# -- Clean up ontology files --
# disorders
import src.data_prep.annont_DISO as diso
# genes
import src.data_prep.annont_GENE as gene
# anatomy
import src.data_prep.annont_ANAT as anat
# physiological pathways
import src.data_prep.annont_PHYS as phys
# chemicals
import src.data_prep.annont_CHEM as chem

# Create a master template for all the different ontology types
onts = []

# -- Merge --
# left join to nodes
onts = pd.merge(genes, gene.gene_ont, on="id", how="left", indicator=True)

# check if any vars are unmerged.
onts._merge.value_counts()

# find missing terms; spot-check if there's any patterns.
missing = onts[onts._merge == 'left_only'][['id', 'node_name']].sort_values(['id'])
print(missing)

# Count frequency of GO terms
onts.go_id.value_counts()

# Count number of GO terms per ID.
onts.groupby('id')['go_id'].count().describe()
