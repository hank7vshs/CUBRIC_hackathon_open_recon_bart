#!/usr/bin/python3
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE
"""
i2i_invertcontrast — Image-to-image (i2i) contrast inversion example.

This module demonstrates the simplest possible Open Recon application:
it receives reconstructed magnitude images and returns contrast-inverted
copies.  It does not use BART and serves as a minimal starting template
for image-to-image workflows.

Entry point called by server.py:
    process(connection, ui_data, mrd_header)

    connection  -- MRD connection; iterate to receive Image/Acquisition
                   messages, send results via connection.send_image().
    ui_data     -- dict of UI parameters from the scanner / test client.
    mrd_header  -- parsed MRD XML header.

Processing pipeline:
    * Accumulate magnitude images by series.
    * Invert contrast: output = maxVal - input,
      where maxVal = 2^BitsStored - 1  (e.g. 4095 for 12-bit).
    * sendOriginalBoolId=true: return the unmodified input instead.
"""

# Based on: https://github.com/kspaceKelvin/python-ismrmrd-server/blob/master/invertcontrast.py

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

        # Process any remaining group of image data.  This can happen if the
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
    """Invert the contrast of a group of magnitude images.

    Applies:  output = maxVal - input
    where maxVal = 2^BitsStored - 1  (typically 4095 for 12-bit scanner data).

    If sendOriginalBoolId is True, the unmodified input images are returned instead.

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
    """Contrast-inversion implementation called by process_image()."""

    logging.info('-----------------------------------------------')
    logging.info('     process_image called with %d images', len(img_group))
    logging.info('-----------------------------------------------')

    # Extract image data into a 5D array of size [img cha z y x]
    # Note: The MRD Image class stores data as [cha z y x]
    data = np.stack([img.data for img in img_group])
    head = [img.getHead()    for img in img_group]
    meta = [ismrmrd.Meta.deserialize(img.attribute_string) for img in img_group]

    # Reformat data to [y x z cha img], i.e. [row col] for the first two dimensions
    data = data.transpose((3, 4, 2, 1, 0))

    logging.debug("Original image data is size %s", data.shape)
    if os.path.exists(DEBUG_FOLDER):
        np.save(DEBUG_FOLDER + "/" + "imgOrig.npy", data)

    # Determine max value from bit depth (12 or 16 bit)
    BitsStored = mrdhelper.get_userParameterLong_value(mrd_header, "BitsStored")
    if BitsStored is None:
        BitsStored = 12
    maxVal = 2**BitsStored - 1

    # Normalize and convert to int16
    data = data.astype(np.float64)
    data *= maxVal / data.max()
    data = np.around(data)
    data = data.astype(np.int16)

    # Invert image contrast
    data = maxVal - data
    data = np.abs(data)

    if os.path.exists(DEBUG_FOLDER):
        np.save(DEBUG_FOLDER + "/" + "imgInverted.npy", data)

    # Re-slice back into individual 2D images
    imagesOut = [None] * data.shape[-1]
    for iImg in range(data.shape[-1]):
        # Transpose from convenience shape [y x z cha] to MRD Image shape [cha z y x]
        imagesOut[iImg] = ismrmrd.Image.from_array(data[..., iImg].transpose((3, 2, 0, 1)), transpose=False)

        # Copy the original header and update data_type to match the new array
        oldHeader = head[iImg]
        oldHeader.data_type = imagesOut[iImg].data_type
        imagesOut[iImg].setHead(oldHeader)

        # Update ISMRMRD Meta attributes
        tmpMeta = meta[iImg]
        tmpMeta['DataRole']                      = 'Image'
        tmpMeta['ImageProcessingHistory']        = ['PYTHON', 'INVERT']
        tmpMeta['WindowCenter']                  = str((maxVal + 1) / 2)
        tmpMeta['WindowWidth']                   = str((maxVal + 1))
        tmpMeta['SequenceDescriptionAdditional'] = 'FIRE'
        tmpMeta['Keep_image_geometry']           = 1

        # Add image orientation directions if not already present
        if tmpMeta.get('ImageRowDir') is None:
            tmpMeta['ImageRowDir'] = ["{:.18f}".format(oldHeader.read_dir[0]),
                                      "{:.18f}".format(oldHeader.read_dir[1]),
                                      "{:.18f}".format(oldHeader.read_dir[2])]

        if tmpMeta.get('ImageColumnDir') is None:
            tmpMeta['ImageColumnDir'] = ["{:.18f}".format(oldHeader.phase_dir[0]),
                                         "{:.18f}".format(oldHeader.phase_dir[1]),
                                         "{:.18f}".format(oldHeader.phase_dir[2])]

        imagesOut[iImg].attribute_string = tmpMeta.serialize()

    # Return original (unmodified) images instead of the inverted ones
    if mrdhelper.get_json_param(ui_data, 'sendOriginalBoolId', default=False, type='bool'):
        logging.info('Returning original unmodified images (sendOriginalBoolId=True)')
        for image in img_group:
            tmpMeta = ismrmrd.Meta.deserialize(image.attribute_string)
            tmpMeta['Keep_image_geometry'] = 1
            image.attribute_string = tmpMeta.serialize()
        return list(img_group)

    return imagesOut
