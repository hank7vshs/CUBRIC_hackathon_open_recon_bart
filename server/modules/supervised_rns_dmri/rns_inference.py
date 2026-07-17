#!/usr/bin/python3
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE
"""
rns_inference — toolbox-specific adapter for supervised_rns_dmri.

Keeps everything that touches Supervised_RNS_dMRI / mrd2nii / nifti2mrd out of
supervised_rns_dmri.py, which stays MRD-protocol-only. Every function here is
pure: MRD/nibabel/numpy objects in, MRD/nibabel/numpy objects out -- no
connection, no sockets -- so each stage can be unit-tested standalone the same
way server/test_RSN.py already validates the toolbox itself.

STATUS: scaffold only, all four functions are stubs. See
hackathon_test/RNS_Module_Integration_Plan.md step 6 for the full breakdown
and status of each stage.

Pipeline (client sends ISMRMRD in, live module path, no intermediate files):

    img_group, mrd_header
        -> mrd_to_nifti()        -- ISMRMRD -> NIfTI, in-memory
        -> extract_dwi_aux()     -- bval/bvec/mask out of the MRD stream
        -> run_inference()       -- RNS-trained model, inference only
        -> nifti_to_mrd_images() -- NIfTI -> ISMRMRD, in-memory
    -> list[ismrmrd.Image]
"""

import logging

import ismrmrd
import nibabel as nib
import numpy as np


def mrd_to_nifti(img_group, mrd_header):
    """Convert a group of MRD Images into an in-memory NIfTI volume.

    TODO:
      1. `from mrd2nii.mrd2nii_main import mrd2nii_volume`
      2. `nii, sidecar = mrd2nii_volume(mrd_header, img_group)`
      3. Return `nii` (a nibabel image). `sidecar` (BIDS JSON metadata) is
         probably not needed downstream but keep it around for logging.

    mrd2nii_volume() is already in-memory (no disk I/O) -- see the plan doc
    for why this is the case and how it groups slices via the `repetition`
    header field.
    """
    raise NotImplementedError("mrd_to_nifti: see TODO -- call mrd2nii_volume(mrd_header, img_group)")


def extract_dwi_aux(img_group, ui_data):
    """Pull bval/bvec/brain-mask out of the incoming MRD stream.

    TODO: this is blocked on the still-open step-3 encoding decision in the
    plan doc -- MRD has no native field for any of these. Candidates:
      * per-image `user_float`/`user_int` arrays (native ImageHeader fields,
        no Meta/userParameterLong needed) keyed by each image's `repetition`
      * a JSON sidecar delivered via `ui_data`
    Whichever is chosen here must match how the .h5 test files get built.

    Returns:
        (bval, mask_nii) -- bval as a 1D numpy array, mask_nii as an
        in-memory nibabel image.
    """
    raise NotImplementedError("extract_dwi_aux: bval/bvec/mask MRD encoding not yet decided (plan step 3)")


def run_inference(dwi_nii, bval, mask_nii):
    """Fit the RNS-trained model to a DWI volume. Inference only, never trains.

    TODO (ported from Supervised_RNS_dMRI/workflow/scripts/run_model_fitting.py,
    which is a Snakemake `script:` block and not importable as-is -- this is
    the reference implementation to port, not a library to call):
      1. Load `model/trained_rf.pkl` + `model/model_information.pkl` once,
         cache at module level (globals below), not per-request.
      2. Reshape the masked volume into [n_voxels, n_volumes] the same way
         run_model_fitting.py does (ROI = I.reshape(...); signal = ROI[mask==1, :]).
      3. For SANDI: compute the direction-averaged (powder-averaged) signal
         upstream of this -- see SphericalMeanFromSH.py / llsFitSH.py in the
         toolbox, not yet inspected.
      4. Call apply_RF_python(signal, trainedML, log) -- confirmed pure:
         numpy array + unpickled model dict in, numpy array out. Vendor this
         ~15-line function directly rather than fighting Snakemake's
         script-import path.
      5. Derive the SANDI-specific parameters (fneurite/fsoma/fextra, see
         run_model_fitting.py) and reshape each back into a 3D array.
      6. Wrap each parametric map as an in-memory nib.Nifti1Image (reuse
         dwi_nii's / mask_nii's affine) and return them.

    Returns:
        dict[str, nib.Nifti1Image] -- one entry per fitted parameter, e.g.
        {"fneurite": ..., "fsoma": ..., "fextra": ...}.
    """
    raise NotImplementedError("run_inference: port apply_RF_python() call from run_model_fitting.py")


def nifti_to_mrd_images(result_niis, img_group):
    """Convert fitted parametric maps back into MRD Images for the client.

    TODO:
      1. Refactor nifti2mrd.py's convert_nifti_to_ismrmrd() so it accepts an
         already-loaded nib.Nifti1Image directly (it currently hard-requires
         a file path via nib.load(nifti_path)) -- small change since that
         file is ours, not a third-party dependency.
      2. Call it once per entry in result_niis, reusing geometry/orientation
         metadata from img_group (the original incoming images) rather than
         re-deriving it.
      3. Return a flat list[ismrmrd.Image], one (or one series) per fitted
         parameter -- following the reslicing pattern used in
         i2i_invertcontrast._process_image_impl().
    """
    raise NotImplementedError("nifti_to_mrd_images: refactor convert_nifti_to_ismrmrd() to take an in-memory nib.Nifti1Image")
