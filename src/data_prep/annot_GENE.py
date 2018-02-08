# annot_GENE.py
# Cleans up all gene ontology annotations based on the Gene Ontology Consortium's classification
# Laura Hughes, lhughes@scripps.edu, 29 January 2018
#
# Data sources: https://github.com/flaneuse/ntwk-explr/blob/master/datain/DATA_README.md


# Setup
import pandas as pd
import warnings
import requests
import progressbar
from src.data_prep.clean_neo4j import get_nodes


# Pull unique nodes from Nuria's graph
nodes = get_nodes()

gene_ids = nodes[nodes.node_type == 'GENE']

df = trans_result['entrez_dict']

def get_geneterms(gene_ids, transl_url = 'http://mygene.info/v3/query?q=', transl_params = {'entrezonly':'true'}):
    missing = []
    annots = pd.DataFrame()

    with progressbar.ProgressBar(max_value = max(gene_ids.index)) as bar:
        for idx, gene in gene_ids.iterrows():
            if(idx % 50 == 0):
                print(idx)

            gene_id = gene['node_id']
            trans_result = query_translator(gene_id, transl_url = 'http://mygene.info/v3/query?q=', transl_params = {'entrezonly':'true'})
            if(len(trans_result['missing']) > 0):
                print("missing = missing.append(trans_result['missing'])")
            else:
                gene_dict = trans_result['entrez_dict']
                annot = query_geneterms(gene_dict)
                annots = pd.concat([annots, annot])

            bar.update(idx)

    return({'annots': annots, 'missing': missing})




def query_translator(gene_id, transl_url = 'http://mygene.info/v3/query?q=', transl_params = {'entrezonly':'true'}, verbose = False):
    missing = []
    entrez_dict = {}

    curr_params = transl_params.copy()

    if(gene_id.find('NCBIGene') >= 0):
        # NCBIGene already set up to do the annotation query, just needs to remove excess in string
        entrez_dict.update({gene_id: gene_id.replace('NCBIGene:', '')})
        return({'missing': missing, 'entrez_dict': entrez_dict})
    elif ((gene_id.find('UniProt') >= 0 )| (gene_id.find('InterPro') >= 0) | (gene_id.find('RGD') >= 0)):
        # formatting is fine, just needs to be combined
        gene_query = transl_url + gene_id
    elif (gene_id.find('FlyBase') >= 0):
        # formatting is fine, just needs to be combined
        gene_query = transl_url + gene_id
        # update species id
        curr_params.update({'species': 'fruitfly'})
    elif (gene_id.find('Xenbase') >= 0):
        # formatting is fine, just needs to be combined
        gene_query = transl_url + gene_id
        # update species id
        curr_params.update({'species': 'frog'})
    elif (gene_id.find('ZFIN') >= 0):
        # formatting is fine, just needs to be combined
        gene_query = transl_url + gene_id
        # update species id
        curr_params.update({'species': 'zebrafish'})
    elif (gene_id.find('WormBase') >= 0):
        # formatting is fine, just needs to be combined
        gene_query = transl_url + gene_id
        # update species id
        # params.update({'species': 6239}) C. elegans
        # params.update({'species': 31234}) C. remanei
    elif (gene_id.find('MGI') >= 0):
        gene_query = transl_url + 'mgi:' + gene_id.replace('MGI:', 'MGI\\\\:')
    else:
        if(verbose):
            print('unknown gene ' + gene_id)
        missing.append((gene_id, 'unknown syntax'))
        return({'missing': missing, 'entrez_dict': entrez_dict})

    # run the request to translate the gene id to an Entrez Gene id
    transl = requests.get(gene_query, params = curr_params).json()

    try:
        (transl['total'])
    except:
        if(verbose):
            print('query failed for ' + gene_id)
        missing.append((gene_id, 'bad query'))
    else:
        if(transl['total'] > 1):
            if(verbose):
                print('could not uniquely find gene ' + gene_id)
            missing.append((gene_id, 'not unique'))
        elif(transl['total'] == 0):
            if(verbose):
                print('request ok but could not find ' + gene_id)
            # print(requests.get(gene_query, params = curr_params).url)
            missing.append((gene_id, 'not found'))
        else:
            try:
                entrez_dict.update({gene_id: transl['hits'][0]['entrezgene']})
            except:
                missing.append((gene_id, '??? no entrez?'))

    return({'missing': missing, 'entrez_dict': entrez_dict})



def query_geneterms(gene_dict, gene_url = 'https://mygene.info/v3/gene/', gene_params = {'fields':'symbol,name,go'}):
    if(type(gene_dict) != dict):
        raise ValueError('gene id is not supplied as a dictionary. Provide a dict with {<merge_id>: <entrez_id>}')
    GOs = pd.DataFrame()

    for gene_key, entrez_id in gene_dict.items():
        result = requests.get(gene_url + str(entrez_id), params = gene_params).json()

        # If GO terms exist, pull them out
        try:
            result['go']
        except:
            pass
        else:
            for key, value in result['go'].items():
                # if there's a single row, convert it to a list so DataFrame can append properly
                if (type(value) == dict):
                    GO = pd.DataFrame([value])
                else:
                    GO = pd.DataFrame(value)
                GOs = pd.concat([GOs, GO], ignore_index=True)

            GOs['node_id'] = gene_key
            GOs['entrez_id'] = result['_id']
            GOs['symbol'] = result['symbol']
            GOs['gene_name'] = result['name']

        return(GOs)

# Run the query
go = get_geneterms(gene_ids)

missing = pd.DataFrame(go['missing'], columns = ['gene_id', 'reason']).sort_values(['reason', 'gene_id'])
missing['db'] = missing.gene_id.apply(lambda x: x[0:3])

missing.gene_id
missing.groupby('reason').db.value_counts()

len(go['missing'])


# [4] merge to ontology term names and classify into hierarchial levels (not implemented for now) ------------------------------------------------
