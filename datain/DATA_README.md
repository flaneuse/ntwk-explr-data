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

* Annotation sources
HPO: http://compbio.charite.de/jenkins/job/hpo.annotations/lastStableBuild/
MP: http://www.informatics.jax.org/downloads/reports/index.html#pheno


# Ontology sources
| node type | ontology source | download file | permalink downloaded file | description | download date | common id |
| --------- | --------- | --------- | --------- | --------- | --------- | --------- |
| disorder | [upheno](https://github.com/obophenotype/upheno) | see "Cross-walk"; from [upheno mammal](https://github.com/obophenotype/upheno/blob/master/mammal.owl), [upheno vertebrate](https://github.com/obophenotype/upheno/blob/master/vertebrate.owl), [upheno metozoa](https://github.com/obophenotype/upheno/blob/master/metazoa.owl) | NA | Combined cross-species phenotype ontologies; incomplete | 2018-01-26 | |
| gene | [Gene Ontology Consortium](http://www.geneontology.org/) | [ontology structure](http://purl.obolibrary.org/obo/go/go-basic.obo),  see "Cross-walk" for annotations | updated daily| using basic version of the GO; filtered such that the graph is guaranteed to be acyclic, and annotations can be propagated up the graph. The relations included are is_a, part_of, regulates, negatively_regulates and positively_regulates | 2018-01-26 | `UniProtKB` (human), `RGD` (rat), `MGI:` (mouse), `FBgn` (fly), `ZDB-GENE-` (zebrafish), `NCBI_GP:` or `PAMGO_VMD:` (oocytes), `WBGene` (worm) |
| pathways | [Reactome](https://reactome.org/download-data) | reactome.graphdb.tgz | NA | Reactome graph database (neo4j format) | 2018-01-25 | Reactome `R-` id |
| anatomy | [uberon](http://uberon.github.io/downloads.html) | uberon/ext.owl | [2017-10-28 version](http://purl.obolibrary.org/obo/uberon/releases/2017-10-28)| "recommended version; imports subsets of other ontologies such as GO, and includes all of the cell ontology (CL)" | 2018-01-24 | `UBERON:` id |
| chemical | [ChEBI](ftp://ftp.ebi.ac.uk/pub/databases/chebi/ontology/) | chebi.owl | [2017-12-31 version](ftp://ftp.ebi.ac.uk/pub/databases/chebi/ontology/chebi.owl) | full ChEBI ontology set | 2018-01-25 | `ChEBI:` id |
### Notes
* Uberpheno has been used by the Human Phenotype ontology group; however, website seems to be defunct.
* Upheno -- while used apparently by the Monarch Initiative -- seems to be just pulling imports of each of the phenotype ontologies together; not sure if it's adding anything, aside from the cross-walk files and the mp-hp alignment equivalents. Better to just get the real deal from the updated sources?

# Cross-walk to unique IDs

http://www.uniprot.org/uploadlists/

## Disorder
| unique ID | description | mapping source | individual phenotype ontology file(s) |
| --------- | --------- | --------- | --------- |
| MP | mammalian phenotype | [upheno](https://github.com/obophenotype/upheno/blob/master/mappings/hp-to-mp-bestmatches.tsv) | [mp](http://purl.obolibrary.org/obo/mp.owl), [mp-hp alignment](http://purl.obolibrary.org/obo/upheno/hp-mp/mp_hp-align-equiv.owl, [mpath: mouse pathology](http://purl.obolibrary.org/obo/upheno/imports/mpath_phenotype.owl) |
| MP | http://purl.obolibrary.org/obo/mp/releases/2018-01-24/mp.owl | http://purl.obolibrary.org/obo/mp.owl |
| FBbt | fly anatomy | NA |
| FBcv | fly controlled vocabulary | NA |
| HP | human phenotype | < base >| [hp](http://purl.obolibrary.org/obo/hp.owl) |
| ZP | zebrafish phenotype | [upheno](https://github.com/obophenotype/upheno/blob/master/mappings/hp-to-zp-bestmatches.tsv) |
| WBPhenotype | *C. elegans* phenotype | [upheno](https://github.com/obophenotype/upheno/blob/master/mappings/hp-to-wbphenotype-bestmatches.tsv)
| DOID | UMD human diseases | |
| OMIM | NCBI Online Mendelian Inheritance in Man (human diseases) | |
| MESH | NCBI medical subject headings | |
| Misc. from upheno | potentially necessary ontologies from other sources | [GO Phenotypes, incl. Cell Ontology](http://purl.obolibrary.org/obo/upheno/imports/go_phenotype.owl), [NBO, neuro behavior ontology](http://purl.obolibrary.org/obo/upheno/imports/nbo_phenotype.owl), [uberon](http://purl.obolibrary.org/obo/upheno/imports/uberon_phenotype.owl) |

## Gene
| unique ID | description | mapping source | individual phenotype ontology file(s) |
| --------- | --------- | --------- | --------- |
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
| GO | gene ontology |[Gene Association file](https://reactome.org/download/current/gene_association.reactome)|
| reactome | Reactome | < base > |
| KEGG | KEGG | ?? |
| ChEBI | Chemical Entities of Biological Interest | [Reactome ChEBI --> Reactome all levels](https://reactome.org/download/current/ChEBI2Reactome_All_Levels.txt)|
| FOODON | Food ontology| NA (only one pathway, whatever) |

## Anatomy
| unique ID | description | mapping source |
| --------- | --------- | --------- |
| Uberon | Uberon cross-species ontology | not needed |

## Chemical
| unique ID | description | mapping source |
| --------- | --------- | --------- |
| ChEBI | ChEBI | not needed |

# Issues
* distinction between phenotypes, diseases; pathways, phenotypes, and ontologies
