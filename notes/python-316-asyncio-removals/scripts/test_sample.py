import asyncio
import pytest
import pytest_asyncio


@pytest_asyncio.fixture
async def fn_value():
    await asyncio.sleep(0)
    yield asyncio.get_running_loop()


@pytest_asyncio.fixture(loop_scope="module", scope="module")
async def mod_loop():
    yield asyncio.get_running_loop()


@pytest.mark.asyncio
async def test_function_scope(fn_value):
    assert fn_value is asyncio.get_running_loop()


@pytest.mark.asyncio(loop_scope="module")
async def test_module_scope_a(mod_loop):
    assert mod_loop is asyncio.get_running_loop()


@pytest.mark.asyncio(loop_scope="module")
async def test_module_scope_b(mod_loop):
    assert mod_loop is asyncio.get_running_loop()


@pytest.mark.asyncio
async def test_gather_and_timeout():
    async def one():
        await asyncio.sleep(0.01)
        return 1
    async with asyncio.timeout(1):
        assert await asyncio.gather(one(), one()) == [1, 1]


def test_sync_after_async():
    assert asyncio.run(asyncio.sleep(0, result=2)) == 2
