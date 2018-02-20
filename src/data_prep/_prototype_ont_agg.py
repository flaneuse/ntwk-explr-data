# @name:        _prototype_ont_agg.py
# @summary:     test out visualizations and aggregations for real prototype NGLY1 pathways
# @description:
# @sources:
# @depends:     ont_dict.py, query_ngly1.py
# @author:      Laura Hughes
# @email:       lhughes@scripps.edu
# @license:     MIT
# @date:        16 February 2018

# [0: setup]  ----------------------------------------------------------------------------------------------------
import pandas as pd
import random
import src.data_prep.query_ngly1 as ngly1


# [1: Pull out all pathways]  -------------------------------------------------------------------------------
all_paths = ngly1.data
all_metapaths = ngly1.metapaths

queries = ngly1.queries.keys()
query = random.sample(queries, 1)[0] # randomly pick a single one


paths = all_paths[query]

metapaths = all_metapaths[all_metapaths['query'] == query]
nodes = paths['nodes']
edges = paths['edges']

# [2: Test some aggregations] ---------------------------------------------------------------------------
nodes.head()

nodes.groupby('node_type').node_name.value_counts()

# [3: merge together datasets] --------------------------------------------------------------------------
