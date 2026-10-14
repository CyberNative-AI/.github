# Stopgap for pytest-asyncio <= 1.4.0 on Python 3.16, which removed the
# asyncio policy API. Remove once a pytest-asyncio release supports 3.16.
import sys

if sys.version_info >= (3, 16):
    import pytest_asyncio.plugin as _pa

    _pa._get_event_loop_policy = lambda: None
    _pa._set_event_loop_policy = lambda policy: None
