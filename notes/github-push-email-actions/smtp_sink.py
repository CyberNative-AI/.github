#!/usr/bin/env python3
"""Accept one SMTP message on 127.0.0.1:<port>, write its DATA to <file>, exit."""
import socket
import sys

port, out = int(sys.argv[1]), sys.argv[2]
srv = socket.create_server(("127.0.0.1", port))
conn, _ = srv.accept()
f = conn.makefile("rwb")


def say(line):
    f.write(line.encode() + b"\r\n")
    f.flush()


say("220 sink")
while True:
    cmd = f.readline().decode().strip()
    verb = cmd.split(" ")[0].upper()
    if verb in ("EHLO", "HELO"):
        say("250 sink")
    elif verb in ("MAIL", "RCPT", "RSET", "NOOP"):
        say("250 ok")
    elif verb == "DATA":
        say("354 end with .")
        data = []
        while (line := f.readline()) not in (b".\r\n", b".\n", b""):
            data.append(line[1:] if line.startswith(b"..") else line)
        open(out, "wb").write(b"".join(data))
        say("250 queued")
    elif verb == "QUIT":
        say("221 bye")
        break
    else:
        say("502 no")
conn.close()
