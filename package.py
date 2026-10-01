"""Create a deterministic complete source ZIP (no credentials or runtime caches).

Usage: python package.py [--output /absolute/path.zip]
"""
import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT=Path(__file__).resolve().parent
EXCLUDED={'work','__pycache__','.git','.venv','.env','.env.local'}


def files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(part in EXCLUDED or part.startswith('.env') for part in p.relative_to(ROOT).parts))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'work/nyc311-python-data-exploration.zip');args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    included=files()
    if args.output.resolve() in [p.resolve() for p in included]:raise ValueError('Output must be outside included source files')
    with ZipFile(args.output,'w',compression=ZIP_DEFLATED,compresslevel=9) as z:
        for p in included:
            info=ZipInfo('nyc311-python-data-exploration/'+p.relative_to(ROOT).as_posix(),date_time=(2024,1,1,0,0,0));info.compress_type=ZIP_DEFLATED;info.external_attr=0o100644<<16
            z.writestr(info,p.read_bytes(),compresslevel=9)
    with ZipFile(args.output) as z:assert z.testzip() is None
    print(f'Packaged {len(included)} files: {args.output} ({args.output.stat().st_size:,} bytes)')


if __name__=='__main__':main()
