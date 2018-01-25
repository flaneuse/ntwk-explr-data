# Data background
Within NGLY1 knowledge graph, there are 7 types of nodes (listed in order of frequency):
* **disorder:** phenotypes
* **gene:** genes or proteins
* **physiology:** physiological pathways
* **anatomy:** organs
* **genotype:** description of a specific individual with traits/phenotype
* **variant:** specific mutation of gene
* **chemical:** small molecule

To categorize these nodes into broader categories, they need to be merged in with ontologies. Focusing on the 5 major sources of nodes: disorders, genes, pathways, anatomy, and chemicals.

# The general protocol
1. Extract unique ids for each group of nodes
2. Cross-walk unique id to common id for each ontology source
3. If necessary, group cross-species ontology terms to standardize.
4. Merge annotation terms with each specific node (disorder, gene, pathway, anatomy, or chemical)
5. Check for unmerged node ids.
6. For every node, collect parents (and associated levels within ontology hierarchy).

# Ontology sources
| node type | ontology source | download file | permalink downloaded file | description | download date | common id |
| --------- | --------- | --------- |
| disorder | [uberpheno]() | <> |
| gene | [GO Central]() | <> |
| pathways | [Reactome]() | <> |
| anatomy | [uberon](http://uberon.github.io/downloads.html) | uberon/ext.owl | [2017-10-28 version](http://purl.obolibrary.org/obo/uberon/releases/2017-10-28)| "recommended version; imports subsets of other ontologies such as GO, and includes all of the cell ontology (CL)" | 2018-01-24 | UBERON: id |
| chemical | [ChEBI]() | ChEBIidD |

# Cross-walk to unique IDs
## Disorder
| unique ID | description | mapping source |
| --------- | --------- | --------- |
| MP | mammalian phenotype | |
| FBbt | fly anatomy | |
| FBcv | fly controlled vocabulary | |
| HP | human phenotype | |
| ZP | zebrafish phenotype | |
| WBPhenotype | *C. elegans* phenotype |
| DOID | UMD human diseases | |
| OMIM | NCBI Online Mendelian Inheritance in Man (human diseases) | |
| MESH | NCBI medical subject headings | |

## Gene
| unique ID | description | mapping source |
| --------- | --------- | --------- |
| NCBIGene | human | |
| ZFIN | zebrafish ||
| Wormbase | *C. elegans* ||
| Xenbase | *Xenopus* oocytes ||
| MGI | mouse ||
| RGD | rat ||
| FlyBase | fly ||
| Uniprot | protein | |
| InterPro | EMBL protein | |

## Pathways
| unique ID | description | mapping source |
| --------- | --------- | --------- |
| GO | gene ontology | |
| reactome | Reactome | |
| KEGG | KEGG ||
| ChEBI | | |
| FOODON | Food ontology| NA (only one pathway, whatever) |

## Anatomy
| unique ID | description | mapping source |
| --------- | --------- | --------- |
| Uberon | Uberon cross-species ontology | not needed |

## Chemical
| unique ID | description | mapping source |
| --------- | --------- | --------- |
| ChEBI | ChEBI | not needed |
