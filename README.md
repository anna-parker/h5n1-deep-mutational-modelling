# H5N1 Deep Mutational Modelling

This repo attempts to reproduce the findings of ["Deep mutational scanning of H5 hemagglutinin to inform influenza virus surveillance"](https://pmc.ncbi.nlm.nih.gov/articles/PMC11584116/) using alphaFold and autoDock.

Deep mutational scanning libraries were designed in the background of the A/American Wigeon/South Carolina/USDA-000345-001/2021 strain, which can be found [here](https://github.com/dms-vep/Flu_H5_American-Wigeon_South-Carolina_2021-H5N1_DMS/blob/main/library_design/pH2rU3_ForInd_H5_H5N1_American_Wigeon_genscript_T7_CMV_ZsGT2APurR.gb) - the H5 AA sequence is in `data/H5_reference.fasta`.

## Steps

1. Compute all combinations of single AA position mutations (except for mutations to the stop codon) from the `H5_reference.fasta`. For simplicity I will use what is called `sequential_site` numbering - here the first position in the H5 reference sequence has position 1 and each site's position after that increases incrementally. 

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/create_mutants.py --reference data/H5_reference.fasta
```

2. Run alphaFold2 monomer to infer the structure of the mutated H5 proteins. To reduce runtime we first run alphaFold with the reference H5 and reuse the MSAs that were downloaded during this process for the other mutants. (Downloading MSAs takes roughly 40min). In order to reuse MSAs the msas/ folder must be copied into the folder where the new output is generated and alphafold must be called with the `--use-precomputed-msas` argument. (Sadly I cannot reuse the downloaded PDBs which adds an additional 10min to the runtime). I run alphaFold on the ETH cluster, a script to submit and generate alphafold jobs for each mutant via SLURM can be called using:

```
python scripts/submit_jobs.py --fasta-dir <dir>
```

3. Create a conda env to run autoDock vina: 

```
micromamba create -f environment.yaml -y
micromamba activate autodock
```

4. Prepare the ligand, in this case the [human a2-6-linked receptor](https://pubchem.ncbi.nlm.nih.gov/compound/alpha-Neup5Ac-_2-_6_-beta-D-Galp?utm_source=chatgpt.com#section=InChI) for docking using the SMILES format:

```
git clone git@github.com:forlilab/scrubber.git
cd scrubber
pip install -e .
scrub.py "CC(=O)N[C@@H]1[C@H](C[C@@](O[C@H]1[C@@H]([C@@H](CO)O)O)(C(=O)O)OC[C@@H]2[C@@H]([C@@H]([C@H]([C@@H](O2)O)O)O)O)O" -o ../data/human-ligand-scrubbed.sdf --ph 7
scrub.py "CC(=O)N[C@@H]1[C@H](C[C@@](O[C@H]1[C@@H]([C@@H](CO)O)O)(C(=O)O)O[C@H]2[C@H]([C@H](OC([C@@H]2O)O)CO)O)O" -o ../data/avian-ligand-scrubbed.sdf --ph 7
cd ..
mk_prepare_ligand.py -i data/human-ligand-scrubbed.sdf -o data/human-ligand-scrubbed.pdbqt
mk_prepare_ligand.py -i data/avian-ligand-scrubbed.sdf -o data/avian-ligand-scrubbed.pdbqt
```

5. Prepare the "receptor" (mutated H5 protein in our case):

```
mk_prepare_receptor.py --box_enveloping <mutant>.pdb --padding 1.0 --read_pdb <mutant>.pdb -o <mutant> -p
```

Example using known H5 structure from PDB (note you need to remove the residues/ligands, the script will spit out a list of unprocessable residues which you can then add to the `-d` to be ignored):

```
data = ast.literal_eval(dict_str)
keys_str = ",".join(data.keys())
```

```
mk_prepare_receptor.py --read_pdb data/1MQN.pdb --box_enveloping 1MQN_HA1.pdb --padding 2.0 -o 1MQN -v -p -d C:1,C:2,F:1,F:2,F:3,F:4,I:1,I:2,J:1,K:1,K:2,K:3,K:4,L:1,M:1,M:2,M:3,M:4,A:400,B:400,D:400,D:401,E:400,G:400,G:401,G:406,H:400 --allow_bad_res

mk_prepare_receptor.py --read_pdb data/3UBE.pdb --box_enveloping data/3UBE.pdb --padding 1.0 -o 3UBE -v -p -d M:1,M:2,M:3,N:1,N:2,N:3,O:1,O:2,P:1,P:2,Q:1,Q:2,R:1,R:2,R:3,A:334,A:335,A:336,C:334,E:333,J:561,K:641 --allow_bad_res
```

6. Run the docking calculation:

```
vina --receptor <mutant>.pdbqt --ligand ligand-scrubbed.pdbqt --config <mutant>.box.txt
       --exhaustiveness=100 --out <mutant>_ligand_vina_out.pdbqt
```

Note "The predicted free energy of binding should be about -13 kcal/mol for poses that are similar to the crystallographic pose."