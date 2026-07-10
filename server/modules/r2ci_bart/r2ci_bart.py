#!/usr/bin/python3
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE
"""
r2ci_bart — Raw k-space to complex-image (r2ci) reconstruction using BART.

This is the main module to modify when developing a custom BART reconstruction.

Entry point called by server.py:
    process(connection, ui_data, mrd_header)

    connection  -- MRD connection object; iterate to receive Acquisitions,
                   call connection.send_image() to return results.
    ui_data     -- dict of UI parameters set by the user at the scanner
                   (or from client/debug_ui_data.json during testing).
    mrd_header  -- parsed MRD XML header with scan geometry (matrix, FOV, etc.)

Processing pipeline (see process_raw() for details):
    1. Buffer all k-space readouts for a slice into a [PE x RO x phs x cha] array.
    2. Estimate coil sensitivities with BART's ecalib.
    3. Reconstruct with BART's pics (iterative SENSE / compressed sensing).
    4. Strip oversampling and format output as MRD Image messages.

To add your own BART reconstruction, edit the BART section in process_raw().
"""

# Based on: https://github.com/kspaceKelvin/python-ismrmrd-server/blob/master/bartfire.py

import ismrmrd
import sys
import os
import logging
import traceback
import numpy as np
import ctypes
from src import mrdhelper
from src import constants

# Load BART's Python bindings if the toolbox path is set
if "BART_TOOLBOX_PATH" in os.environ:
    sys.path.insert(0, os.path.join(os.environ["BART_TOOLBOX_PATH"], "python"))

try:
    import bart
except ImportError:
    bart = None  # Deferred error: raised at process() call time if BART is actually needed

# Folder for debug output files
DEBUG_FOLDER = "/tmp/share/debug"


def _is_imaging_readout(acq):
    """Return True if the acquisition is an imaging readout (not noise, calibration, etc.)"""
    return (not acq.is_flag_set(ismrmrd.ACQ_IS_NOISE_MEASUREMENT) and
            not acq.is_flag_set(ismrmrd.ACQ_IS_PARALLEL_CALIBRATION) and
            not acq.is_flag_set(ismrmrd.ACQ_IS_PHASECORR_DATA) and
            not acq.is_flag_set(ismrmrd.ACQ_IS_NAVIGATION_DATA))


def _slice_group_key(acq):
    """Return a tuple that uniquely identifies the logical slice group for buffering.

    Acquisitions sharing the same key belong to the same reconstruction unit
    (same slice, repetition, contrast, average, and set).
    """
    return (
        int(acq.idx.slice),
        int(acq.idx.repetition),
        int(acq.idx.contrast),
        int(acq.idx.average),
        int(acq.idx.set),
    )

def process(connection, ui_data, mrd_header):
    if bart is None:
        raise ImportError(
            "The 'bart' Python module could not be found. "
            "Set BART_TOOLBOX_PATH to the BART installation directory."
        )

    logging.info("ui_data: \n%s", ui_data)

    # mrd_header should be a parsed MRD header object, but may be a plain string
    # if XML parsing failed earlier in server.py
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
    acq_buffers = {}
    try:
        for item in connection:
            # ----------------------------------------------------------
            # Raw k-space data messages
            # ----------------------------------------------------------
            if isinstance(item, ismrmrd.Acquisition) and _is_imaging_readout(item):

                # Buffer per logical slice context to support segmented/interleaved scans.
                key = _slice_group_key(item)  # group by slice, repetition, contrast, average, and set
                if key not in acq_buffers:
                    acq_buffers[key] = []
                acq_buffers[key].append(item)

                # Process slice and send image back to client. Handle averages, contrasts, sets, and repetitions if needed.
                if item.is_flag_set(ismrmrd.ACQ_LAST_IN_SLICE):
                    logging.info("Processing buffered k-space data for key=%s (%d readouts)", key, len(acq_buffers[key]))
                    image = process_raw(acq_buffers[key], ui_data, mrd_header)
                    connection.send_image(image)
                    acq_buffers.pop(key, None)

            # ----------------------------------------------------------
            # Image and waveform data messages are not supported
            # ----------------------------------------------------------
            elif isinstance(item, ismrmrd.Image):
                logging.info("Received an image, but this is not supported -- discarding")
                continue

            elif isinstance(item, ismrmrd.Waveform):
                logging.info("Received a waveform, but this is not supported -- discarding")
                continue

            elif item is None:
                break

            else:
                logging.error("Unsupported data type %s", type(item).__name__)

        # Process any remaining groups of raw or image data.  This can
        # happen if the trigger condition for these groups are not met.
        # This is also a fallback for handling image data, as the last
        # image in a series is typically not separately flagged.
        for key in sorted(acq_buffers.keys()):
            if len(acq_buffers[key]) == 0:
                continue
            logging.info("Processing a group of k-space data (untriggered) for key=%s (%d readouts)", key, len(acq_buffers[key]))
            image = process_raw(acq_buffers[key], ui_data, mrd_header)
            connection.send_image(image)
            acq_buffers.pop(key, None)

    except Exception as e:
        logging.error(traceback.format_exc())
        connection.send_logging(constants.MRD_LOGGING_ERROR, traceback.format_exc())

    finally:
        connection.send_close()

def process_raw(group, ui_data, mrd_header):
    """Reconstruct one slice from a list of MRD Acquisition objects.

    Args:
        group       -- list of ismrmrd.Acquisition for a single slice
        ui_data     -- dict of UI parameters (numCoilIntId, picsFlagsId)
        mrd_header  -- parsed MRD XML header

    Returns:
        list of ismrmrd.Image objects, one per phase encoding step, or an empty
        list if reconstruction fails.
    """
    if len(group) == 0:
        return []

    try:
        return _process_raw_impl(group, ui_data, mrd_header)
    except Exception:
        logging.error("process_raw() failed for group of %d readouts:\n%s", len(group), traceback.format_exc())
        return []


def _process_raw_impl(group, ui_data, mrd_header):
    """Reconstruct one slice — implementation called by process_raw().

    Args:
        group       -- list of ismrmrd.Acquisition for a single slice
        ui_data     -- dict of UI parameters (numCoilIntId, picsFlagsId)
        mrd_header  -- parsed MRD XML header

    Returns:
        list of ismrmrd.Image objects, one per phase encoding step
    """
    # Format data into single [cha PE RO phs] array
    lin = [acquisition.idx.kspace_encode_step_1 for acquisition in group]
    phs = [acquisition.idx.phase                for acquisition in group]

    # Use the zero-padded matrix size
    kspace = np.zeros((group[0].data.shape[0],
                       mrd_header.encoding[0].encodedSpace.matrixSize.y,
                       mrd_header.encoding[0].encodedSpace.matrixSize.x,
                       max(phs)+1),
                      group[0].data.dtype)

    raw_head = [None]*(max(phs)+1)

    for acq, lin, phs in zip(group, lin, phs):
        if (lin < kspace.shape[1]) and (phs < kspace.shape[3]):
            # TODO: Account for asymmetric echo in a better way
            kspace[:,lin,-acq.data.shape[1]:,phs] = acq.data

            # center line of k-space is encoded in user[5]
            if (raw_head[phs] is None) or (np.abs(acq.getHead().idx.kspace_encode_step_1 - acq.getHead().idx.user[5]) < np.abs(raw_head[phs].idx.kspace_encode_step_1 - raw_head[phs].idx.user[5])):
                raw_head[phs] = acq.getHead()

    # Flip matrix in RO/PE to be consistent with ICE
    kspace = np.flip(kspace, (1, 2))

    logging.debug("K-space data is size %s", kspace.shape)

    # Format as [row col phs cha] for BART
    kspace = kspace.transpose((1, 2, 3, 0))

    logging.debug("Raw data is size %s", kspace.shape)
    if os.path.exists(DEBUG_FOLDER):
        np.save(DEBUG_FOLDER + "/" + "raw.npy", kspace)

    # -----------------------------------
    #   Extract data from Open Recon UI
    # -----------------------------------

    # Coils
    num_coils = mrdhelper.get_json_param(ui_data, 'numCoilIntId')
    if num_coils is None:
        num_coils = -1
        logging.error("Failed to find parameter entry 'numCoilIntId'.")
    logging.info("Number of selected coils: %s", num_coils)

    # String with Flags for PICS Tool
    pics_flags = mrdhelper.get_json_param(ui_data, 'picsFlagsId')
    if pics_flags is None:
        pics_flags = " "
        logging.error("Failed to find parameter entry 'picsFlagsId'.")
    logging.info("PICS regularization is set to: %s", pics_flags)

    # -----------------------------------
    #   BART Reconstruction
    #
    #   This is the section to modify for your own reconstruction.
    #   Replace or extend the ecalib/pics calls with any BART command.
    #   See: https://mrirecon.github.io/bart
    # -----------------------------------

    # Optional coil reduction: keep only the first num_coils coils
    if "-1" == str(num_coils):
        logging.info("Using all coils.")
        kspace_cut = kspace
    else:
        logging.info("Reducing to %s coils.", num_coils)
        kspace_cut = bart.bart(1, 'extract 3 0 ' + str(num_coils), kspace)

    # Step 1: Estimate coil sensitivity maps from the k-space center
    sens = bart.bart(1, 'ecalib -m 1', kspace_cut)

    # Step 2: Iterative SENSE reconstruction (pics = parallel imaging + compressed sensing)
    # pics_flags comes from the UI parameter 'picsFlagsId' (e.g. "-e -S" for ESPIRiT)
    reco = bart.bart(1, 'pics ' + str(pics_flags), kspace_cut, sens)

    # -----------------------------------

    logging.debug("Image data is size %s", reco.shape)
    if os.path.exists(DEBUG_FOLDER):
        np.save(DEBUG_FOLDER + "/" + "img.npy", reco)

    # Output should at least have 3 dims
    if 3 > len(np.shape(reco)):
        logging.info("Add singleton axis to data.")
        img = reco[:, :, np.newaxis]
    else:
        img = reco

    # Normalization #FIXME: Check ICE pipeline for exact reproduction of product recon
    img *= 1 / np.max(np.abs(img))

    # Remove readout oversampling
    if mrd_header.encoding[0].reconSpace.matrixSize.x != 0:
        offset = int((img.shape[1] - mrd_header.encoding[0].reconSpace.matrixSize.x) / 2)
        img = img[:, offset:offset+mrd_header.encoding[0].reconSpace.matrixSize.x]

    # Remove phase oversampling
    if mrd_header.encoding[0].reconSpace.matrixSize.y != 0:
        offset = int((img.shape[0] - mrd_header.encoding[0].reconSpace.matrixSize.y) / 2)
        img = img[offset:offset+mrd_header.encoding[0].reconSpace.matrixSize.y, :]

    logging.debug("Image without oversampling is size %s", img.shape)
    if os.path.exists(DEBUG_FOLDER):
        np.save(DEBUG_FOLDER + "/" + "imgCrop.npy", img)

    # Determine max value for windowing (12 or 16 bit)
    BitsStored = mrdhelper.get_userParameterLong_value(mrd_header, "BitsStored")
    if BitsStored is None:
        BitsStored = 12
    maxVal = 2**BitsStored - 1

    # Format as ISMRMRD image data
    imagesOut = []
    for phs in range(img.shape[2]):
        # Create new MRD instance for the processed image
        # img has shape [PE RO phs], i.e. [y x].
        # from_array() should be called with 'transpose=False' to avoid warnings, and when called
        # with this option, can take input as: [cha z y x], [z y x], or [y x]
        tmpImg = ismrmrd.Image.from_array(img[..., phs], transpose=False)

        # Set the header information
        tmpImg.setHead(mrdhelper.update_img_header_from_raw(tmpImg.getHead(), raw_head[phs]))
        tmpImg.field_of_view = (ctypes.c_float(mrd_header.encoding[0].reconSpace.fieldOfView_mm.x),
                                ctypes.c_float(mrd_header.encoding[0].reconSpace.fieldOfView_mm.y),
                                ctypes.c_float(mrd_header.encoding[0].reconSpace.fieldOfView_mm.z))
        tmpImg.image_index = phs

        # Set ISMRMRD Meta Attributes
        tmpMeta = ismrmrd.Meta()
        tmpMeta['DataRole']                         = 'Image'
        tmpMeta['ImageProcessingHistory']           = ['PYTHON', 'BART']
        tmpMeta['WindowCenter']                     = str((maxVal+1)/2)
        tmpMeta['WindowWidth']                      = str((maxVal+1))
        tmpMeta['SequenceDescriptionAdditional']    = 'OPENRECON'
        tmpMeta['Keep_image_geometry']              = 1

        # Add image orientation directions to MetaAttributes if not already present
        if tmpMeta.get('ImageRowDir') is None:
            tmpMeta['ImageRowDir'] = ["{:.18f}".format(tmpImg.getHead().read_dir[0]), "{:.18f}".format(tmpImg.getHead().read_dir[1]), "{:.18f}".format(tmpImg.getHead().read_dir[2])]

        if tmpMeta.get('ImageColumnDir') is None:
            tmpMeta['ImageColumnDir'] = ["{:.18f}".format(tmpImg.getHead().phase_dir[0]), "{:.18f}".format(tmpImg.getHead().phase_dir[1]), "{:.18f}".format(tmpImg.getHead().phase_dir[2])]

        metaXml = tmpMeta.serialize()
        logging.debug("Image MetaAttributes: %s", metaXml)
        logging.debug("Image data has %d elements", tmpImg.data.size)
        tmpImg.attribute_string = metaXml
        imagesOut.append(tmpImg)

    return imagesOut

