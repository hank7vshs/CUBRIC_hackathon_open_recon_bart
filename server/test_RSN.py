'''
Python equivalent of the CLI call
  
  Supervised_RNS_dMRI (the console script) is just a thin wrapper — literally from 
  Supervised_RNS_dMRI.run import main; sys.exit(main()). Tracing run.py:
  
  def main():
      app = SnakeBidsApp(os.path.abspath(os.path.dirname(__file__)),
  configfile_path="config/snakebids.yml")
      app.run_snakemake()
  
  run_snakemake() calls self._app.run(), and _Runner.run() (in
  snakebids/bidsapp/run.py) parses sys.argv[1:] when no explicit args list is given
  — the CLI parsing is driven entirely by sys.argv, not a separate function with
  named parameters. 
  '''

import sys
from Supervised_RNS_dMRI.run import main

sys.argv = [
    "Supervised_RNS_dMRI",
    "/workspaces/CUBRIC_hackathon_open_recon_bart/test/hackathon_data/",
    "/workspaces/CUBRIC_hackathon_open_recon_bart/test/hackathon_data/",
    "participant",
    "--force-output",
    "--path-dwi", "/workspaces/CUBRIC_hackathon_open_recon_bart/test/hackathon_data/sub-{subject}_dwi.nii.gz",
    "--Model", "SANDI",
    "--Delta", "23.6",
    "--Small_Delta", "7",
    "--cores", "all",
    "-np",          # drop this once the dry-run looks right
]
main()


