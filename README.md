# H5N1 Deep Mutational Modelling

This repo aims to reproduce the findings of ["Deep mutational scanning of H5 hemagglutinin to inform influenza virus surveillance"](https://pmc.ncbi.nlm.nih.gov/articles/PMC11584116/) using alphaFold and diffDock.

Deep mutational scanning libraries were designed in the background of the A/American Wigeon/South Carolina/USDA-000345-001/2021 strain, which can be found [here](https://github.com/dms-vep/Flu_H5_American-Wigeon_South-Carolina_2021-H5N1_DMS/blob/main/library_design/pH2rU3_ForInd_H5_H5N1_American_Wigeon_genscript_T7_CMV_ZsGT2APurR.gb) - the H5 AA sequence is in `data/H5_reference.fasta`.

## Steps

1. Compute all combinations of single AA position mutations (except for mutations to the stop codon) from the `H5_reference.fasta`. For simplicity I will use what is called `sequential_site` numbering - here the first position in the H5 reference sequence has position 1 and each site's position after that increases incrementally. 

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/create_mutants.py --reference data/H5_reference.fasta
```
