# Corporate/Custom CA Certificates

If you're behind a corporate proxy (like Zscaler, Blue Coat, etc.) or need custom CA certificates, place them here.

## For macOS with Zscaler

1. Export the Zscaler Root CA from Keychain:
   ```bash
   security find-certificate -a -p -c "Zscaler Root CA" /Library/Keychains/System.keychain > .devcontainer/certs/zscaler-root.crt
   ```

2. Or export all system certificates:
   ```bash
   security export -t certs -f pemseq -k /Library/Keychains/System.keychain -o .devcontainer/certs/system-certs.pem
   ```

3. Rebuild the dev container

## For Windows

Things work out of the box.

## File Format

- Files must have `.crt` or `.pem` extension
- Must be in PEM format (text-based, starts with `-----BEGIN CERTIFICATE-----`)
