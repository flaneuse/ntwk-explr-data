import pandas as pd
import os

output_dir = 'dataout/' # path within Atom notebook

ont_ids = ['FBcv', 'wbphenotype', 'FBbt', 'UBERON', 'mp', 'hp', 'go', 'CHEBI']

ont_ids = { 'GENE':['go'],
    'DISO': ['FBcv', 'wbphenotype', 'FBbt', 'mp', 'hp'],
    'ANAT': ['UBERON'],
    'CHEM': ['CHEBI']
    }

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
# !! TODO: ignore_index / index = id
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

ont_dicts.columns

dupes = ont_dicts.loc[ont_dicts.duplicated(subset=['id', 'node_type']), ['node_type', 'ont_id', 'id']].sort_values('id')
dupes = ont_dicts.loc[ont_dicts.duplicated(subset=['id']), ['node_type', 'ont_id', 'id']].sort_values('id')

dupes.node_type.value_counts()



ont_dicts[ont_dicts.id == 'UPHENO:0001002']
