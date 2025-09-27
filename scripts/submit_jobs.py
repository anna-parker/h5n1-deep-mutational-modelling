#!/usr/bin/env python3
import argparse
import re
import shutil
import subprocess
from pathlib import Path
import sys

PATTERN = re.compile(r"^H5_(\d{1,3})([A-Za-z])\.fasta$")  # H5_<pos><char>.fasta


def copy_contents(src_dir: Path, dst_dir: Path):
    """Copy *contents* of src_dir into dst_dir (not the src folder itself)."""
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Reference msas folder not found: {src_dir}")
    dst_dir.mkdir(parents=True, exist_ok=True)
    for item in src_dir.iterdir():
        target = dst_dir / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def render_template(template_path: Path, name: str) -> str:
    text = template_path.read_text()
    return text.replace("{{name}}", name)


def submit_sbatch(script_path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(["sbatch", str(script_path)], capture_output=True, text=True)


def process_file(
    fasta_file: Path,
    ref_msas: Path,
    template_slurm: Path,
    out_root: Path,
    dry_run: bool = False,
):
    m = PATTERN.match(fasta_file.name)
    if not m:
        return None  # not a match
    pos = int(m.group(1))
    if not (1 <= pos <= 200):
        return None
    char = m.group(2)
    name = f"H5_{pos}{char}"

    job_dir = out_root / name
    msas_dir = job_dir / "msas"
    job_dir.mkdir(parents=True, exist_ok=True)

    # 1) Copy contents of reference msas into target msas
    copy_contents(ref_msas, msas_dir)

    # 2) Render slurm script
    slurm_text = render_template(template_slurm, name)
    slurm_out = Path(out_root) / f"{name}.slurm"
    slurm_out.write_text(slurm_text, encoding="utf-8")

    # 3) Submit with sbatch
    if not dry_run:
        res = submit_sbatch(slurm_out)
        return {
            "name": name,
            "job_dir": str(job_dir),
            "stdout": res.stdout.strip(),
            "stderr": res.stderr.strip(),
            "returncode": res.returncode,
        }
    else:
        return {
            "name": name,
            "job_dir": str(job_dir),
            "stdout": "(dry-run) sbatch not executed",
            "stderr": "",
            "returncode": 0,
        }


def main():
    ap = argparse.ArgumentParser(
        description="Prepare per-mutation folders, copy MSA contents, render Slurm scripts, and submit with sbatch."
    )
    ap.add_argument(
        "--fasta-dir",
        default="fasta-files",
        help="Directory containing H5_<pos><char>.fasta files.",
    )
    ap.add_argument(
        "--reference-msas",
        default="H5_reference/msas",
        help="Folder whose contents are copied into each job's msas/",
    )
    ap.add_argument(
        "--template",
        default="template.slurm",
        help="Path to the Slurm template containing {{name}}.",
    )
    ap.add_argument(
        "--out-root",
        default=".",
        help="Root directory to create H5_<pos><char> folders in (default: current).",
    )
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Do everything except file copies and sbatch submission.",
    )
    args = ap.parse_args()

    fasta_dir = Path(args.fasta_dir)
    ref_msas = Path(args.reference_msas)
    template_slurm = Path(args.template)
    out_root = Path(args.out_root)

    if not fasta_dir.is_dir():
        print(f"ERROR: fasta-dir not found: {fasta_dir}", file=sys.stderr)
        sys.exit(2)
    if not template_slurm.is_file():
        print(
            f"ERROR: template slurm file not found: {template_slurm}", file=sys.stderr
        )
        sys.exit(2)

    results = []
    for path in sorted(fasta_dir.iterdir()):
        if not path.is_file():
            continue
        try:
            info = process_file(
                fasta_file=path,
                ref_msas=ref_msas,
                template_slurm=template_slurm,
                out_root=out_root,
                dry_run=args.dry_run,
            )
            if info:
                results.append(info)
                msg = (
                    f"[OK] {info['name']} -> {info['stdout']}"
                    if info["returncode"] == 0
                    else f"[ERR] {info['name']} -> {info['stderr']}"
                )
                print(msg)
        except Exception as e:
            print(f"[EXC] {path.name}: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
