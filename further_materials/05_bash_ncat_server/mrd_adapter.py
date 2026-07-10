"""MRD/ISMRMRD/BART format adapter.

Subcommands:
  python3 mrd_adapter.py receive  output.h5       — read MRD from stdin, save acquisitions to h5
  python3 mrd_adapter.py send     input.h5        — read h5 images, write MRD to stdout
  python3 mrd_adapter.py h5tocfl  input.h5 prefix — extract k-space from h5 → BART CFL
  python3 mrd_adapter.py cfltoh5  prefix output.h5— convert BART CFL → ISMRMRD h5 image
"""
import sys, struct, numpy as np, ismrmrd

# MRD message IDs
CONFIG_FILE  = 1
CONFIG_TEXT   = 2
METADATA_XML = 3
CLOSE        = 4
TEXT         = 5
ACQUISITION  = 1008
IMAGE        = 1022
WAVEFORM     = 1026

def read_exact(n):
    buf = b''
    while len(buf) < n:
        chunk = sys.stdin.buffer.read(n - len(buf))
        if not chunk:
            raise EOFError("Unexpected end of MRD stream")
        buf += chunk
    return buf

def receive(out_h5):
    """Read MRD messages from stdin, save XML header and acquisitions to h5."""
    dset = ismrmrd.Dataset(out_h5, "dataset", True)
    while True:
        id_bytes = sys.stdin.buffer.read(2)
        if len(id_bytes) < 2:
            break
        msg_id = struct.unpack('<H', id_bytes)[0]

        if msg_id == CONFIG_FILE:
            read_exact(1024)
        elif msg_id == CONFIG_TEXT:
            length = struct.unpack('<I', read_exact(4))[0]
            read_exact(length)
        elif msg_id == METADATA_XML:
            length = struct.unpack('<I', read_exact(4))[0]
            xml_data = read_exact(length)
            dset.write_xml_header(xml_data.split(b'\x00', 1)[0])
        elif msg_id == TEXT:
            length = struct.unpack('<I', read_exact(4))[0]
            read_exact(length)
        elif msg_id == ACQUISITION:
            dset.append_acquisition(ismrmrd.Acquisition.deserialize_from(read_exact))
        elif msg_id == IMAGE:
            ismrmrd.Image.deserialize_from(read_exact)  # consume, discard
        elif msg_id == WAVEFORM:
            ismrmrd.Waveform.deserialize_from(read_exact)  # consume, discard
        elif msg_id == CLOSE:
            break
        else:
            raise ValueError(f"Unknown MRD message ID: {msg_id}")
    dset.close()

def send(in_h5):
    """Read h5 images, write MRD image messages + close to stdout."""
    out = sys.stdout.buffer
    dset = ismrmrd.Dataset(in_h5, "dataset", False)
    for grp in dset.list():
        if not (grp.startswith('image_') or grp.startswith('images_')):
            continue
        for i in range(dset.number_of_images(grp)):
            image = dset.read_image(grp, i)
            out.write(struct.pack('<H', IMAGE))
            image.serialize_into(out.write)
    out.write(struct.pack('<H', CLOSE))
    out.flush()
    dset.close()

def h5tocfl(in_h5, out_prefix):
    """Extract k-space from ISMRMRD h5 → BART CFL."""
    dset = ismrmrd.Dataset(in_h5, "dataset", False)
    n = dset.number_of_acquisitions()
    acqs = [dset.read_acquisition(i) for i in range(n)]
    dset.close()

    # Filter imaging readouts (skip noise, calibration, phase correction)
    acqs = [a for a in acqs if not (
        a.is_flag_set(ismrmrd.ACQ_IS_NOISE_MEASUREMENT) or
        a.is_flag_set(ismrmrd.ACQ_IS_PARALLEL_CALIBRATION) or
        a.is_flag_set(ismrmrd.ACQ_IS_PHASECORR_DATA))]

    ncha = acqs[0].active_channels
    nro = acqs[0].number_of_samples
    npe = max(a.idx.kspace_encode_step_1 for a in acqs) + 1

    kspace = np.zeros((nro, npe, 1, ncha), dtype=np.complex64)
    for a in acqs:
        kspace[:, a.idx.kspace_encode_step_1, 0, :] = a.data.T

    dims = [1] * 16
    dims[0], dims[1], dims[2], dims[3] = nro, npe, 1, ncha
    with open(f"{out_prefix}.hdr", "w") as f:
        f.write("# Dimensions\n" + " ".join(str(d) for d in dims) + "\n")
    kspace.T.astype(np.complex64).tofile(f"{out_prefix}.cfl")

def cfltoh5(cfl_prefix, out_h5):
    """Convert BART CFL result → ISMRMRD h5 image."""
    with open(f"{cfl_prefix}.hdr") as f:
        f.readline()  # skip comment
        dims = [int(d) for d in f.readline().split()]
    data = np.fromfile(f"{cfl_prefix}.cfl", dtype=np.complex64)
    img = data.reshape(dims[::-1]).T.squeeze()  # Fortran → C order

    mx = np.max(np.abs(img))
    if mx > 0:
        img = img / mx

    if img.ndim == 2:
        img = img[np.newaxis, np.newaxis, :, :]
    elif img.ndim == 3:
        img = img[np.newaxis, :, :, :]

    image = ismrmrd.Image.from_array(img.astype(np.complex64), transpose=False)
    image.image_type = ismrmrd.IMTYPE_COMPLEX

    dset = ismrmrd.Dataset(out_h5, "dataset", True)
    dset.append_image("image_0", image)
    dset.close()

if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'receive':
        receive(sys.argv[2])
    elif cmd == 'send':
        send(sys.argv[2])
    elif cmd == 'h5tocfl':
        h5tocfl(sys.argv[2], sys.argv[3])
    elif cmd == 'cfltoh5':
        cfltoh5(sys.argv[2], sys.argv[3])
    else:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
