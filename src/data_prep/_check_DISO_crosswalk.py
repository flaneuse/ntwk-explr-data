# @name: check_DISO_crosswalk.py
# @title: Looks at whether disorder ontology terms can be successfully merged with each other.
# @description: From what I can tell, there are 2 projects to try to do a cross-organism ontology crosswalk.
#               • UberPheno was done by some of the same people who work on the Human phenotype ontology. However, it's defunct and website is AWOL.
#               • [upheno](https://github.com/obophenotype/upheno) is used by Monarch and has created a series of crosswalks b/w organisms.
#                 However, it doesn't look like it's been maintained in the past 2 years.
#                 Wanted to check first if there's any sense trying to standardize phenotype names b/w orgnaisms.
# @summary:     No.  Not worth it.  Phenoytpes should be organism-specific.
# @author: Laura Hughes
# @email: lhughes@scripps.edu
# @date: 14 February 2018

import pandas as pd

# --- mammalian ---
# Mammalian Phenotype project: all terms
mp_core = pd.read_csv('dataout/2018-02-09_mp_terms.tsv', sep='\t')
# Pull out just the terms named w/ MP id:
mp_core['type'] = mp_core.id.apply(lambda x: x[0:2])
sum(mp_core.type == 'MP')
# MP TOTAL IN ONTOLOGY: 12335

# crosswalk
mp = pd.read_csv('datain/ontology/DISOdict_hp-to-mp-bestmatches.tsv', sep='\t', header=None)
len(mp) # 10834 entries in total; however, many are duplicate "best-matches"
len(pd.unique(mp[2]))
# MP SUMMARY: only 1925 / 12335 (~ 16%) have a match.


# --- C. elegans ---
# Mammalian Phenotype project: all terms
wb_core = pd.read_csv('dataout/2018-02-09_wbphenotype_terms.tsv', sep='\t')
# Pull out just the terms named w/ MP id:
wb_core['type'] = wb_core.id.apply(lambda x: x[0:2])
sum(wb_core.type == 'WB')
# MP TOTAL IN ONTOLOGY: 2442

# crosswalk
wb = pd.read_csv('datain/ontology/DISOdict_hp-to-wbphenotype-bestmatches.tsv', sep='\t', header=None)
len(wb) # 1491 entries in total; however, many are duplicate "best-matches"
len(pd.unique(wb[2]))
# WORM SUMMARY: only 45 / 2442 (~ 2%) have a match.

z = pd.read_csv('datain/ontology/DISOdict_hp-to-zp-bestmatches.tsv', sep='\t', header=None)

# NOTE: no fly cross-walk.
# Not surprising that cross-organism phenotype doesn't have good standardization; what does "curly wings" mean w.r.t. humans?
