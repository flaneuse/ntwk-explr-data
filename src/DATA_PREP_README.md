# Data Preparation README
See also [data pipeline diagram](https://docs.google.com/presentation/d/1dk_1lTGAhB1tJZuUH9yfJoAZwznedHM_DHrCVFBqeW8/edit?usp=sharing)

## Purpose of data preparation directory
* Assemble a lookup dictionary for every node the the NGLY1 network containing its id, name, description, and associated level within its particular ontology
* Create a pathway json file for specific queries of the network
* Merge pathways/ontology levels

## Run order of files
*all within `data_prep/`*
* `ont_struct.py`: parses ontology structures within the [Ontology Lookup Service](https://www.ebi.ac.uk/ols/ontologies) to get the levels of each ontology term within the network
* `clean_neo4j.py`: helper functions to pull nodes and paths
  * `annot_GENE.py`: calls `clean_neo4j.py` to get unique nodes in network; converts gene IDs to list of ontology terms
  * `ont_dict.py`: calls `clean_neo4j.py` and `ont_struct.py` to get unique nodes in network; merges in ontology data
