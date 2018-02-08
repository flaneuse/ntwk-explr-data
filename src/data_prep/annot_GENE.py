# annot_GENE.py
# Cleans up all gene ontology annotations based on the Gene Ontology Consortium's classification
# Laura Hughes, lhughes@scripps.edu, 29 January 2018
#
# Data sources: https://github.com/flaneuse/ntwk-explr/blob/master/datain/DATA_README.md


# [0] Setup -----------------------------------------------------------------------------------------------------------------------------
import pandas as pd
import warnings
import requests
import progressbar
import src.data_prep.clean_neo4j as neo4j

output_dir = 'dataout/'

# [1] Set up functions to call mygene.info API and pull out the annotation terms per gene -----------------------------------------------

# TODO: Could be combined into single API query: http://mygene.info/v3/query?q=mgi:MGI\\:95574&fields=name,symbol,go
# <<< get_geneterms(gene_ids, transl_url = 'http://mygene.info/v3/query?q=', transl_params = {'entrezonly':'true'}) >>>
# @description: outer most function to gather all the gene annotation terms for a given id.
#               First translates gene ID into standardized NCBI Entrez gene IDs; then gathers all the annotation terms for each unique gene.
# @example:     get_geneterms(pd.DataFrame({'node_id': ['MGI:1857807', 'RGD:628763', 'NCBIGene:698835', 'ZFIN:ZDB-GENE-080418-1', 'MGI:5797368']}))
# @input:       *gene_ids*: dataframe containing the gene ids in column `node_id`
#               *transl_url*: base of the mygene.info url query
#               *transl_params*: extra params to feed into API. By default, only include genes which have an entrez id (since it'll be used for the query)
# @output:      list containing:
#               *annots*: dataframe containing the annotation data (columns: entrez_id, gene_name, ont_id, )
#               *missing*: info about the missing data, where mygene.info was unable to convert the ID into an Entrez Gene.
#                       columns: gene_id (input), reason (why query failed), id_type (1st 3 letters of inputted gene id)
#                       Note that this does *not* catch genes without annotation info, since that's biologically reasonable.

def get_geneterms(gene_ids, transl_url = 'http://mygene.info/v3/query?q=', transl_params = {'entrezonly':'true'}):
    missing = pd.DataFrame()
    annots = pd.DataFrame()

    with progressbar.ProgressBar(max_value = max(gene_ids.index)) as bar:
        for idx, gene in gene_ids.iterrows():

            gene_id = gene['node_id']
            trans_result = query_translator(gene_id, transl_url = 'http://mygene.info/v3/query?q=', transl_params = {'entrezonly':'true'})
            if(len(trans_result['missing']) > 0):
                missing = pd.concat([missing, trans_result['missing']], ignore_index=True)
            else:
                gene_dict = trans_result['entrez_dict']
                annot = query_geneterms(gene_dict)
                annots = pd.concat([annots, annot], ignore_index=True)
            if (idx % 10 == 0):
                bar.update(idx)

    # Sort the missing values
    missing = missing.sort_values(['reason', 'id_type', 'gene_id'])

    return({'annots': annots, 'missing': missing})



# <<< query_translator(gene_id, transl_url = 'http://mygene.info/v3/query?q=', transl_params = {'entrezonly':'true'}, verbose = False) >>>
# @description: single call to mygene.info to translate gene_id into an Entrez Gene ID
# @example:     query_translator('RGD:628763')
# @input:       *gene_id*: string containing a single gene id.
#               *transl_url*: base of the mygene.info url query
#               *transl_params*: extra params to feed into API. By default, only include genes which have an entrez id (since it'll be used for the query)
#               *verbose*: binary if the function should print errors.
# @output:      list containing:
#               *entrez_dict*: dict consisting of inputted gene id: matched entrez gene id
#               *missing*: info about the missing data, if mygene.info was unable to convert the ID into an Entrez Gene.
#                       columns: gene_id (input), reason (why query failed), id_type (1st 3 letters of inputted gene id)
#                       Note that this does *not* catch genes without annotation info, since that's biologically reasonable.
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

    # convert missing to DataFrame
    missing = pd.DataFrame(missing, columns = ['gene_id', 'reason'])
    missing['id_type'] = missing.gene_id.apply(lambda x: x[0:3]) # pulls out first three letters of the gene_id

    return({'missing': missing, 'entrez_dict': entrez_dict})


# <<< query_geneterms(gene_dict, gene_url = 'https://mygene.info/v3/gene/', gene_params = {'fields':'symbol,name,go'}) >>>
# @description: single call to mygene.info to pull annotation terms for a specific entrezgene ID
# @example:     query_geneterms({'RGD:628763': '286758'})
# @input:       *gene_dict*: output of query_translator; dict containing id: matched id (entrez id)
#               *gene_url*: base of the mygene.info url query
#               *gene_params*: extra params to feed into API. By default, only include symbol, name, and go terms
# @output:      DataFrame containing: symbol, name, GO terms
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

# [2] Find the relevant gene IDs -----------------------------------------------
# Pull unique nodes from Nuria's graph
nodes = neo4j.get_nodes()

gene_ids = nodes[nodes.node_type == 'GENE']


# [3] Run the query ------------------------------------------------------------
go = get_geneterms(gene_ids)

# [4] Check for missing terms --------------------------------------------------
missing = go['missing']
if (len(missing)):
    print(str(len(missing)) + " ids not converted to Entrez Gene IDs")
    print(missing.groupby('reason').id_type.value_counts())
missing.to_csv(output_dir + str(pd.Timestamp.today().strftime('%F')) + "_NGLY1noentrezid.txt")



# [5] merge to ontology term names and classify into hierarchial levels (not implemented for now) ------------------------------------------------
