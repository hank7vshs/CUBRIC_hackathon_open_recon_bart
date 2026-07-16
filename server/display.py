# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE

import h5py
import numpy as np
import argparse

def view(file_path='out.h5'):
    with h5py.File(file_path, "r") as f:
        a_group_key = list(f.keys())[-1]
        group = f[a_group_key]
        image_keys = sorted(k for k in group.keys() if k.startswith('image_'))
        if not image_keys:
            raise KeyError(f"No image_* group found under '{a_group_key}'")
        image_key = image_keys[0]
        dset = group[image_key]['data']
        arr = dset[()]

        if dset.dtype.names and 'real' in dset.dtype.names and 'imag' in dset.dtype.names:
            real = np.array(arr['real'])
            imag = np.array(arr['imag'])
            image = np.sqrt(real**2 + imag**2)
        elif np.iscomplexobj(arr):
            image = np.abs(arr)
        else:
            image = np.abs(arr)

        print(np.shape(image))

        import matplotlib.pyplot as plt
        plt.imshow(image[0,0,0,:,:].T, cmap='gray')
        plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Visualizes MRD output files for example data.")
    parser.add_argument("file", help="Path to MRD file")
    args = parser.parse_args()

    view(args.file)
