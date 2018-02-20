# @name: ont_PHYS.py
# @description:  Pulls out the Reactome graph network and gets the hierarchical structure
# @source: https://reactome.org/ContentService/
# @author: Laura Hughes
# @email: lhughes@scripps.edu
# @date: 7 February 2018

import requests
import pandas as pd

url = "https://reactome.org/ContentService/data/pathways/top/9606"
url = "https://reactome.org/ContentService/data/pathways/low/entity/1640170/allForms?species=9606"
resp = requests.get(url)

len(resp.json())

resp.json()[0]
