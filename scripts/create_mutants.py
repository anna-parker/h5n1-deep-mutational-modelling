#!/usr/bin/env python3
from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
from pathlib import Path
import argparse

STANDARD_AA = list("ACDEFGHIKLMNPQRSTVWY")

def generate_mutants(record, outdir, prefix="H5_"):
    """
    For each position in record.seq, generate all 19 mutants and
    write each as a separate FASTA file named <prefix><pos><Mut>.fasta.
    """
    seq = str(record.seq).upper()
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    total = 0
    for pos, wt in enumerate(seq, start=1):  # 1-based positions
        if wt not in STANDARD_AA:
            continue
        for mut in STANDARD_AA:
            if mut == wt:
                continue
            mutant_record = SeqRecord(
                Seq(seq[:pos-1] + mut + seq[pos:]),
                id=f"{prefix}{pos}{mut}",
                description=f"{record.id} position {pos} {wt}->{mut}"
            )
            filename = outdir / f"{prefix}{pos}{mut}.fasta"
            with open(filename, "w") as fh:
                SeqIO.write(mutant_record, fh, "fasta")
            total += 1
    return total

def main():
    parser = argparse.ArgumentParser(
        description="Generate all single AA mutants."
    )
    parser.add_argument("--reference", help="Input reference fasta file")
    parser.add_argument("-o", "--outdir", default="mutants", help="Output directory.")
    parser.add_argument("--prefix", default="H5_", help="Filename prefix (default: H5_).")
    args = parser.parse_args()

    record = next(SeqIO.parse(args.reference, "fasta"))
    total = generate_mutants(record, args.outdir, args.prefix)
    print(f"Generated {total} mutant FASTA files in {Path(args.outdir).resolve()}")

if __name__ == "__main__":
    main()
