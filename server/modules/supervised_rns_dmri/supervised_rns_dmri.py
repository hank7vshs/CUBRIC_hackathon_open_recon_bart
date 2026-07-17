#!/usr/bin/python3
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE
"""
supervised_rns_dmri — Diffusion MRI model fitting via Realistic Noise
Synthesis (RNS), using https://github.com/Bradley-Karat/Supervised_RNS_dMRI.

STATUS: scaffold only. process_image() currently passes images through
unmodified. The model-fitting pipeline is not wired in yet -- see the
TODOs in _process_image_impl() below.

This is an image-to-image (i2i) module: it receives pre-reconstructed
diffusion-weighted magnitude images (already reconstructed by ICE) and
returns derived parametric maps, following the same connection/series
accumulation pattern as i2i_invertcontrast.

Entry point called by server.py:
    process(connection, ui_data, mrd_header)

    connection  -- MRD connection; iterate to receive Image/Acquisition
                   messages, send results via connection.send_image().
    ui_data     -- dict of UI parameters from the scanner / test client.
    mrd_header  -- parsed MRD XML header.

The actual toolbox integration lives in rns_inference.py (mrd_to_nifti,
extract_dwi_aux, run_inference, nifti_to_mrd_images), kept separate from
this file so each stage is testable with plain arrays/objects, no MRD
connection needed. See hackathon_test/RNS_Module_Integration_Plan.md step 6
for the full breakdown and per-stage status.

Open design decisions (resolve before wiring rns_inference into
_process_image_impl):
    * How do bval/bvec/brain-mask/noisemap reach this module? MRD has no
      native field for any of them. Candidates: per-image userParameter
      entries, or a JSON sidecar delivered via ui_data. Whichever is
      chosen must match how the .h5 test files are built. This is
      rns_inference.extract_dwi_aux()'s job.
    * rns_inference.run_inference() calls apply_RF_python() -- the
      confirmed inference-only entry point -- not the
      training/analyze_all_datasets path, which is far too slow for a
      per-request reconstruction call. Training happens offline; only the
      trained pickle files (e.g. trained_rf.pkl, modelinfo.pkl) ship
      inside the module, under model/.
"""

import ismrmrd
import os
import logging
import traceback
import numpy as np
from src import mrdhelper
from src import constants

# Folder for debug output files
DEBUG_FOLDER = "/tmp/share/debug"


def process(connection, ui_data, mrd_header):
    logging.info("ui_data: \n%s", ui_data)

    try:
        logging.info("Incoming dataset contains %d encodings", len(mrd_header.encoding))
        logging.info("First encoding is of type '%s', with a matrix size of (%s x %s x %s) and a field of view of (%s x %s x %s)mm^3",
            mrd_header.encoding[0].trajectory,
            mrd_header.encoding[0].encodedSpace.matrixSize.x,
            mrd_header.encoding[0].encodedSpace.matrixSize.y,
            mrd_header.encoding[0].encodedSpace.matrixSize.z,
            mrd_header.encoding[0].encodedSpace.fieldOfView_mm.x,
            mrd_header.encoding[0].encodedSpace.fieldOfView_mm.y,
            mrd_header.encoding[0].encodedSpace.fieldOfView_mm.z)

    except Exception:
        logging.info("Improperly formatted mrd_header: \n%s", mrd_header)

    # Continuously parse incoming data parsed from MRD messages
    current_series = 0
    img_group = []
    try:
        for item in connection:
            # ----------------------------------------------------------
            # Image data messages
            # ----------------------------------------------------------
            if isinstance(item, ismrmrd.Image):
                # When the series index changes, process the accumulated group.
                # For a DWI series this group is expected to hold every
                # diffusion volume (one MRD Image per volume) belonging
                # to the same acquisition.
                if item.image_series_index != current_series:
                    logging.info("Processing a group of images because series index changed to %d", item.image_series_index)
                    current_series = item.image_series_index
                    image = process_image(img_group, ui_data, mrd_header)
                    if image:
                        connection.send_image(image)
                    img_group = []

                # Only process magnitude images -- send phase images back without modification
                # (fallback for images with unknown type)
                if (item.image_type is ismrmrd.IMTYPE_MAGNITUDE) or (item.image_type == 0):
                    img_group.append(item)
                else:
                    tmpMeta = ismrmrd.Meta.deserialize(item.attribute_string)
                    tmpMeta['Keep_image_geometry'] = 1
                    item.attribute_string = tmpMeta.serialize()
                    connection.send_image(item)
                    continue

            # ----------------------------------------------------------
            # Raw k-space and waveform data are not supported by this module
            # ----------------------------------------------------------
            elif isinstance(item, ismrmrd.Acquisition):
                logging.info("Received a raw k-space acquisition, but this module only accepts images -- discarding")
                continue

            elif isinstance(item, ismrmrd.Waveform):
                logging.info("Received a waveform, but this is not supported -- discarding")
                continue

            elif item is None:
                break

            else:
                logging.error("Unsupported data type %s", type(item).__name__)

        # Process any remaining group of image data. This can happen if the
        # trigger condition (series index change) is not met for the last series.
        if len(img_group) > 0:
            logging.info("Processing a group of images (untriggered)")
            image = process_image(img_group, ui_data, mrd_header)
            if image:
                connection.send_image(image)
            img_group = []

    except Exception as e:
        logging.error(traceback.format_exc())
        connection.send_logging(constants.MRD_LOGGING_ERROR, traceback.format_exc())

    finally:
        connection.send_close()


def process_image(img_group, ui_data, mrd_header):
    """Fit the RNS-trained model to a group of DWI magnitude images.

    Returns an empty list if processing fails.
    """
    if len(img_group) == 0:
        return []

    try:
        return _process_image_impl(img_group, ui_data, mrd_header)
    except Exception:
        logging.error("process_image() failed for group of %d images:\n%s", len(img_group), traceback.format_exc())
        return []


def _process_image_impl(img_group, ui_data, mrd_header):
    """Model-fitting implementation called by process_image().

    TODO: once rns_inference.py's four stages are implemented, replace the
    pass-through body below with:

        dwi_nii = rns_inference.mrd_to_nifti(img_group, mrd_header)
        bval, mask_nii = rns_inference.extract_dwi_aux(img_group, ui_data)
        result_niis = rns_inference.run_inference(dwi_nii, bval, mask_nii)
        return rns_inference.nifti_to_mrd_images(result_niis, img_group)

    Not wired in yet -- all four rns_inference functions currently raise
    NotImplementedError, and process_image()'s exception handler would
    turn that into "zero images returned" for every request. Left as a
    pass-through until enough of the pipeline is real to be worth the
    behavior change. See rns_inference.py and
    hackathon_test/RNS_Module_Integration_Plan.md step 6 for per-stage
    status.

    For now this is a pass-through: it returns the input images
    unmodified so the module is testable end-to-end before the model
    fitting logic is wired in.
    """

    logging.info('-----------------------------------------------')
    logging.info('     process_image called with %d images', len(img_group))
    logging.info('-----------------------------------------------')

    if os.path.exists(DEBUG_FOLDER):
        data = np.stack([img.data for img in img_group])
        np.save(DEBUG_FOLDER + "/" + "imgOrig.npy", data)

    # TODO: replace this pass-through with the RNS model-fitting pipeline.
    for image in img_group:
        tmpMeta = ismrmrd.Meta.deserialize(image.attribute_string)
        tmpMeta['Keep_image_geometry'] = 1
        image.attribute_string = tmpMeta.serialize()

    return list(img_group)
