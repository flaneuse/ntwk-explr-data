# @name:        ont_checkunique.py
# @title:       check if ont IDs are unique (before merge)
# @description: Ont dictionary terms need to be merged with their term ID populated within the knowledge graph.
#               However, ontologies don't stick to a single ontology ID; the Mammalian Phenotype ontology, for instance,
#               uses MP:xxxxx as its core term base, but also incorporates HP:, GO:, etc. terms. So: need to check where
#               there is overlap between the "unique" ids for each ontology dataset.
# @author:      Laura Hughes
# @email:       lhughes@scripps.edu
# @date:        13 February 2018

# [0] Setup -------------------------------------------------------------------------------------------
import pandas as pd
import os

output_dir = 'dataout/' # path within Atom notebook

ont_ids = { 'GENE':['go'],
    'DISO': ['FBcv', 'wbphenotype', 'FBbt', 'mp', 'hp'],
    'ANAT': ['UBERON'],
    'CHEM': ['CHEBI']
    }

# [1] Read in files -------------------------------------------------------------------------------------------
files = sorted(os.listdir(output_dir))

# little helper to see if file has already been generated.
def check_exists(files, ont_id, file_type):
    file_name = [file_name for idx, file_name in enumerate(files) if ont_id + '_' + file_type in file_name]
    if(len(file_name) == 1):
        return file_name[0]
    elif (len(file_name) > 1):
        return file_name[-1]
    else:
        return False

ont_dicts = pd.DataFrame()
for ont_type, ont_ids in ont_ids.items():
    print('\n\n---' + ont_type + '---')
    for ont_id in ont_ids:
        print('\n*' + ont_id + '*')

        # -- terms --
        term_file = check_exists(files, ont_id, 'terms')
        if(term_file):
            # file already exists; read it in
            print('reading in term file')
            ont_dict = pd.read_csv(output_dir + term_file, sep = '\t')
            ont_dict['ont_id'] = ont_id
            ont_dict['node_type'] = ont_type
            ont_dicts = pd.concat([ont_dict, ont_dicts], ignore_index=True)


# [3] Count the duplicates -------------------------------------------------------------------------------------------

# pull the values for the duplicated ids
# Can't use ID alone; 35,127 dupes
sum(ont_dicts.duplicated(subset=['id']))

# Potential option: use the node_type (DISO, GENE, PHYS, CHEM, ANAT)
dupes = ont_dicts.loc[ont_dicts.duplicated(subset=['id']), ['node_type', 'ont_id', 'id']].sort_values('id')
dupes.node_type.value_counts()
dupes.ont_id.value_counts()

# ID + node_type doesn't work; overlap w/i phenotype (DISO) categories
# down to 19,108 duplicates
dupes = ont_dicts.loc[ont_dicts.duplicated(subset=['id', 'node_type']), ['node_type', 'ont_id', 'id']].sort_values('id')
dupes.shape
dupes.node_type.value_counts()
dupes.ont_id.value_counts()

# THE WINNER: ID + ont_id:
dupes = ont_dicts.loc[ont_dicts.duplicated(subset=['id', 'ont_id']), ['node_type', 'ont_id', 'id']].sort_values('id')
dupes.shape

# double checking MP is okay (seems to be the weirdo.)
mp = ont_dicts[ont_dicts.ont_id == 'mp']

sum(mp.duplicated(subset='id'))
