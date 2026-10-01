"""Offline end-to-end reproduction using the included pinned source."""
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parent


def main():
    steps=[]
    commands=[['analysis.py'],['validate.py'],['-m','unittest','discover','-s','tests','-v'],['visualize.py'],['notebook.py'],['build_site.py']]
    for args in commands:
        subprocess.run([sys.executable,*args],cwd=ROOT,check=True)
        steps.append({'command':'python '+' '.join(args),'status':'passed'})
    node=shutil.which('node')
    if node:
        subprocess.run([node,'tests/explorer.test.cjs'],cwd=ROOT,check=True)
        steps.append({'command':'node tests/explorer.test.cjs','status':'passed'})
    else:steps.append({'command':'node tests/explorer.test.cjs','status':'skipped','reason':'Node not installed; browser interactions not checked in this run'})
    result={'status':'passed' if node else 'Python passed; JavaScript skipped','python':platform.python_version(),'platform':platform.system(),'steps':steps,'source_mode':'offline pinned ZIP; no API request','browser_execution':False,'jupyter_kernel_execution':False}
    (ROOT/'results/reproduction.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
