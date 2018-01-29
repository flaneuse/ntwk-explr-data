# ont_GENE.py
# Cleans up all gene ontology sources, based on the Gene Ontology Consortium's classification
# Laura Hughes, lhughes@scripps.edu, 29 January 2018
#
# Data sources: https://github.com/flaneuse/ntwk-explr/blob/master/datain/DATA_README.md

# Gene ontology sources are broken down by

# Setup
import pandas as pd
import warnings
base_dir = "datain/ontology/"

# -- import function --
# [1] import files & [2] add in source info ------------------------------------------------

# <<< importGO >>> : reads in ont file from GO, adds in the source info.
def importGO(file_name, base_dir, n_skip = 0):

    date_pattern = '[0-9]+/[0-9]+/[0-9][0-9][0-9][0-9]'

# Find how many lines to skip; header rows before the real stuff
    while True:
        try:
            ont = pd.read_table(base_dir + file_name, skiprows=n_skip, header=None)
        except:
            n_skip += 1
        else:
            # header fields: http://geneontology.org/page/go-annotation-file-format-20
            col_names = ['db', 'db_id', 'db_symbol', 'qualifier',
            'go_id', 'db_ref', 'evidence_code', 'with_from',
            'go_root', 'obj_name', 'obj_syn', 'obj_type',
            'taxon', 'date', 'assigned', 'annot_ext', 'gene_prod_id'
            ]

            if ont.shape[1] == len(col_names):
                # rename columns
                ont.columns = col_names

                # TODO: deal with qualifier
                ont[ont.qualifier != 'NOT']

                # remove unnecessary columns
                ont.drop(['db_ref', 'evidence_code', 'obj_type', 'date', 'assigned'], axis=1, inplace=True)

            else:
                warnings.warn("unrecognized number of columns; manually rename columns and filter `qualifier` column")

            break

# Pull out the source date and name from the header of the file.
    try:
        header = pd.read_table(base_dir + file_name, nrows=n_skip -1, header=None)
    except:
        # mouse file has a tab-delimited list at the bottom; must skip over.
        header = pd.read_table(base_dir + file_name, nrows=28, header=None)

    source_date = header[0].str.findall(date_pattern)[header[0].str.lower().str.contains('submission date:')]
    ont['ont_date'] = source_date.to_string(index = False, header = False)

    source = header[0].str.replace('!Project_name: ', '')[header[0].str.contains('Project_name:')]

    ont['ont_source'] = source.to_string(index = False, header = False)


    return ont


# import files
human = importGO('GENE_goa_human.gaf', base_dir)
rat = importGO('GENE_gene_association.rgd', base_dir)
mouse = importGO('GENE_gene_association.mgi', base_dir)
fly = importGO('GENE_gene_association.fb', base_dir)
zfish = importGO('GENE_gene_association.zfin', base_dir)
worm = importGO('GENE_gene_association.wb', base_dir)


# [3] convert to mergeable IDs -------------------------------------------------
# To merge properly, unique ids should be in following format:
# HUMAN: `UniProt:P55087`
human['id'] = 'UniProt:' + human.db_id.astype(str)

# RAT: `RGD:620449`
rat['id'] = rat.db.astype(str) + ':' + rat.db_id.astype(str)

# MOUSE: `MGI:96646`
mouse['id'] = mouse.db_id

# FLY: `FlyBase:FBgn0033010`
fly['id'] = 'FlyBase:' + fly.db_id.astype(str)

# ZEBRAFISH: `ZFIN:ZDB-GENE-040426-2931`
zfish['id'] = zfish.db.astype(str) + ':' + zfish.db_id.astype(str)

# WORM: `WormBase:WBGene00013111`
worm['id'] = worm.db.astype(str) + ':' + worm.db_id.astype(str)

# [4] merge to ontology term names and classify into hierarchial levels (not implemented for now) ------------------------------------------------


# [5] append all organisms together ------------------------------------------------
gene_ont = human.append(rat, ignore_index = True).append(mouse, ignore_index = True).append(fly, ignore_index = True).append(zfish, ignore_index = True).append(worm, ignore_index = True)

gene_ont.head
