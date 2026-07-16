#!/usr/bin/python3
# Copyright Siemens Healthineers AG
# License-Identifier: see LICENSE
"""
server.py — Entry point for the Open Recon Python server.

Opens a TCP socket on port 9002, waits for exactly one client connection
(the Open Recon platform or the test client), reads the MRD message stream,
and dispatches reconstruction to the selected processing module.

Usage:
    python3 server.py --or-module r2ci_bart
    python3 server.py --or-module i2i_invertcontrast
"""

from src import constants
from src import connection
import importlib
import argparse
import socket
import logging
import json
import sys
import signal

import ismrmrd.xsd

class Server:

    def __init__(self, address, port, or_module):
        logging.info("Starting server and listening for data at %s:%d", address, port)

        try:
            self.module = importlib.import_module(f"modules.{or_module}")
        except ModuleNotFoundError as e:
            raise ModuleNotFoundError(
                f"Processing module 'modules.{or_module}' could not be found. "
                f"Ensure a valid module folder exists under server/modules/."
            ) from e

        self.address = address
        self.port = port
        self.or_module = or_module
        self.socket = None

    def serve(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.address, self.port))
        logging.debug("Serving... ")
        self.socket.listen(0)

        # Open Recon protocol: one connection per container lifetime
        sock, (remote_addr, remote_port) = self.socket.accept() # generates new socket object "sock"

        logging.info("Accepting connection from: %s:%d", remote_addr, remote_port)

        self.handle(sock)

        logging.info("Finished handling")

        self.socket.close() # Ensure closing "self.socket" object

    def handle(self, sock):

        try:
            # Create a Connection object that wraps the socket and handles MRD message framing.
            # False = do not save incoming data to disk (set True for debugging).
            c = connection.Connection(sock, False)

            # Message 1: reconstruction config (filename or inline text).
            # In Open Recon this carries the application spec identifier.
            config = next(c)

            # Guard: client connected but immediately closed without sending data
            if config is None and c.is_exhausted is True:
                logging.info("Connection closed without any data received")
                return

            # Message 2: MRD XML header describing the scan (matrix size, FOV, etc.)
            mrd_header_xml = next(c)
            logging.debug("XML mrd_header: %s", mrd_header_xml)
            try:
                mrd_header = ismrmrd.xsd.CreateFromDocument(mrd_header_xml)
                if mrd_header.acquisitionSystemInformation.systemFieldStrength_T is not None:
                    logging.info("Data is from a %s %s at %1.1fT", mrd_header.acquisitionSystemInformation.systemVendor, mrd_header.acquisitionSystemInformation.systemModel, mrd_header.acquisitionSystemInformation.systemFieldStrength_T)
            except Exception:
                logging.warning("mrd_header is not a valid MRD XML structure. Passing on as text")
                mrd_header = mrd_header_xml

            # Message 3 (Open Recon only): JSON UI parameters set by the user at the scanner.
            # In the test client these come from client/debug_ui_data.json.
            ui_data = {}
            if c.peek_mrd_message_identifier() == constants.MRD_MESSAGE_TEXT:
                ui_data_text = next(c)
                logging.info("Received UI data: %s", ui_data_text)
                c.save_additional_config(ui_data_text)
                try:
                    ui_data = json.loads(ui_data_text)
                except Exception:
                    logging.error("Failed to parse UI data as JSON")

            # Hand off the connection and header to the selected processing module.
            # The module reads remaining MRD messages (Acquisitions or Images) from
            # the connection iterator and sends results back via connection.send_image().
            module = self.module
            module.process(c, ui_data, mrd_header)

        except Exception as e:
            logging.exception(e)

        finally:
            c.shutdown_close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--or-module",
        choices=["i2i_invertcontrast", "r2ci_bart", "supervised_rns_dmri"],
        help="Processing module to use."
    )
    args = parser.parse_args()
    logging.info(f"Selected Open Recon processing module: {args.or_module}")
    # Create a dispatcher to handle incoming connections
    server = Server('0.0.0.0', 9002, or_module=args.or_module)

    # Trap signal interrupts (e.g. ctrl+c, SIGTERM) and gracefully stop
    def handle_signals(signum, frame):
        logging.info("Received signal interrupt -- stopping server")
        if server.socket is not None:
            server.socket.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_signals)
    signal.signal(signal.SIGINT,  handle_signals)

    server.serve()

if __name__ == '__main__':

    fmt='%(asctime)s - %(message)s\r'

    logging.basicConfig(format=fmt, level=logging.WARNING)
    logging.root.setLevel(logging.DEBUG)
    
    main()