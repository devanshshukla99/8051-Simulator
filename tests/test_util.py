import pytest

from core.util import comparehex, construct_hex, decompose_byte, get_bytes, ishex, sanatize_hex, twos_complement


@pytest.mark.parametrize(
    "val1, val2, result",
    [
        ("0x01", "0x12", False),
        ("0x45", "0x45", True),
        ("0xfa", "0xaf", False),
        ("0x92", "0x91", False),
        ("0xfc", "0xfc", True),
    ],
)
def test_comparehex(val1, val2, result):
    assert comparehex(val1, val2) is result


@pytest.mark.parametrize("val, result", [("0x12", "0xee"), ("0x2e", "0xd2")])
def test_twos_complement(val, result):
    assert twos_complement(val) == result


@pytest.mark.parametrize(
    "val1, val2, result",
    [("0x12", "0xee", "0x12ee"), ("0x2e", "0xd2", "0x2ed2"), ("0xf1", "0x1d", "0xf11d"), ("0x00", "0x45", "0x0045")],
)
def test_construct_hex(val1, val2, result):
    assert construct_hex(val1, val2) == result


@pytest.mark.parametrize(
    "val, result1, result2",
    [("0x12ee", "0x12", "0xee"), ("0x2ed2", "0x2e", "0xd2"), ("0xf11d", "0xf1", "0x1d"), ("0x0045", "0x00", "0x45")],
)
def test_decompose_hex(val, result1, result2):
    assert decompose_byte(val) == [result1, result2]


@pytest.mark.parametrize(
    "val, result",
    [("0x12", 1), ("0x2ed2", 2), ("0xf11d", 2), ("0x00", 1)],
)
def test_get_bytes(val, result):
    assert get_bytes(val) == result


@pytest.mark.parametrize(
    "val, result",
    [
        ("0x12", True),
        ("2ed2", True),
        ("zur", False),
        ("mvi", False),
        ("0x00", True),
        ("0xff", True),
        ("0x124f", True),
        ("1248H", True),
        ("0000H", True),
    ],
)
def test_is_hex(val, result):
    assert ishex(val) is result


@pytest.mark.parametrize("val, result", [("0x12", "12"), ("0Xfa", "fa")])
def test_sanatize_hex(val, result):
    assert sanatize_hex(val) == result
