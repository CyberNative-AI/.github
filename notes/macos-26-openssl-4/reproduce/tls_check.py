"""Handshake on localhost: server presents leaf, client uses ssl.create_default_context(cafile=CA)."""
import socket, ssl, sys, threading
ca, crt, key = sys.argv[1:4]
srv = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); srv.load_cert_chain(crt, key)
ls = socket.socket(); ls.bind(("127.0.0.1", 0)); ls.listen(1); port = ls.getsockname()[1]
def serve():
    c, _ = ls.accept()
    try: srv.wrap_socket(c, server_side=True).close()
    except Exception: c.close()
threading.Thread(target=serve, daemon=True).start()
cli = ssl.create_default_context(cafile=ca)
try:
    with socket.create_connection(("127.0.0.1", port)) as s, cli.wrap_socket(s, server_hostname="localhost"):
        print("handshake OK")
except ssl.SSLCertVerificationError as e:
    print("handshake FAIL:", e.verify_message)
