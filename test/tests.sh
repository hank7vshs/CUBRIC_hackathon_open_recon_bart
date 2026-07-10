# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE
#
# -------------------------------------------
# Define the tests HERE!
# They need to follow the structure:
#   <error-margin> <OR-mode: [i2i_invertcontrast/r2ci_bart]> <data> <ref-reco> <test speed: [slow/fast]>

TESTS=(
    # r2ci_bart: GRE single-slice, Cartesian, fully sampled
    # Verifies the default PICS reconstruction (ecalib + pics -e -S) on gradient-echo data.
    "1e-6 r2ci_bart gre_r2ci.h5 gre_pics_default_reco.h5 fast"

    # r2ci_bart: TSE single-slice, Cartesian, fully sampled
    # Same pipeline on spin-echo data. Broader coverage of the k-space assembly path.
    "1e-6 r2ci_bart tse_r2ci.h5 tse_pics_default_reco.h5 fast"

    # r2ci_bart: TSE interleaved multi-slice, Cartesian
    # Tests correct slice-interleaving handling in the k-space buffering logic.
    "6e-6 r2ci_bart tse_r2ci_interleaved.h5 tse_interleaved_pics_default_reco.h5 fast"

    # i2i_invertcontrast: TSE images sent as MRD Image messages, contrast inversion
    # Verifies the invertcontrast pipeline on pre-reconstructed magnitude images
    # (the normal i2i workflow: images arrive already reconstructed by ICE).
    "1e-6 i2i_invertcontrast tse_i2i.h5 tse_i2i_invertcontrast_reco.h5 fast"

    # i2i_invertcontrast: sendOriginalBoolId=true — passthrough mode
    # Verifies that enabling sendOriginalBoolId returns the original unmodified
    # images instead of the contrast-inverted result.
    # Input is taken directly from ref/ — no copy in data/ needed.
    # With sendOriginalBoolId=true (set in debug_ui_data.json) the output must
    # be identical to the input, so the reference is the input file itself.
    "1e-10 i2i_invertcontrast ref/tse_i2i_invertcontrast_reco.h5 ref/tse_i2i_invertcontrast_reco.h5 fast debug_ui_data_passthrough"
)
# -------------------------------------------
