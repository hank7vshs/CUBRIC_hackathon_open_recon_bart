
#!/usr/bin/python3
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE

import h5py
import argparse
import sys
import numpy as np

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def get_data(file_path):
    try:
        with h5py.File(file_path, 'r') as f:

            # Find the top-level group that contains image data.
            # client.py appends a new timestamped group each run (even on failure),
            # so pick the last group that actually has image_* or images_* subgroups.
            a_group_key = None
            image_groups = []
            for key in reversed(list(f.keys())):
                candidate = [k for k in f[key].keys() if k.startswith('image_') or k.startswith('images_')]
                if candidate:
                    a_group_key = key
                    image_groups = candidate
                    break

            if a_group_key is None:
                raise KeyError("No image_* group found")

            image_group = image_groups[0]

            data_node = f[a_group_key][image_group]['data']

            if isinstance(data_node, h5py.Group):
                if 'real' in data_node and 'imag' in data_node:
                    real = np.array(data_node['real'][:])
                    imag = np.array(data_node['imag'][:])
                    data = real + 1j * imag
                else:
                    raise KeyError("Unsupported complex data layout in image data group")
            else:
                if data_node.dtype.fields and 'real' in data_node.dtype.fields and 'imag' in data_node.dtype.fields:
                    real = np.array(data_node['real'][:])
                    imag = np.array(data_node['imag'][:])
                    data = real + 1j * imag
                else:
                    data = np.array(data_node[:])

            return data

    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

# Calculate NRMSE of absolute difference of datasets
def nrmse_dataset(file_path, ref_path):

    data = get_data(file_path)
    ref  = get_data(ref_path)

    # Cast to float only for non-complex data to avoid int overflow during squaring.
    # Complex arrays already use float internally (complex64/complex128).
    if not np.issubdtype(data.dtype, np.complexfloating):
        data = data.astype(float)
    if not np.issubdtype(ref.dtype, np.complexfloating):
        ref = ref.astype(float)

    rms_ref = np.sqrt(np.mean(np.abs(ref)**2))
    if rms_ref == 0:
        raise ValueError("Reference data has zero RMS — cannot normalize.")

    return np.sqrt(np.mean(np.abs(data - ref)**2)) / rms_ref
   

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compute the NRMSE between two HDF5 image files and check it against a threshold.")
    parser.add_argument("eps", help="Limit of NRMSE for passing")
    parser.add_argument("filename", help="Path to the HDF5 (.h5) file")
    parser.add_argument("refname", help="Path to the HDF5 (.h5) reference file")
    args = parser.parse_args()

    nrmse = nrmse_dataset(args.filename, args.refname)

    if float(args.eps) > nrmse:
        print(f"{bcolors.OKGREEN}{nrmse}\t{args.eps}\tTest passed successfully!{bcolors.ENDC}")
        exit(0)
    else:
        print(f"{bcolors.FAIL}{nrmse}\t{args.eps}.{bcolors.ENDC}")
        print(f"{bcolors.FAIL}\tError while comparing dataset {args.filename} with reference { args.refname}!{bcolors.ENDC}")
        exit(1)
    



