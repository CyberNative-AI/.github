import s3
if not s3._open:
    raise RuntimeError("registration closed")
