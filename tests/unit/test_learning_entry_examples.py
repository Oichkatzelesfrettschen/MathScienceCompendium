"""Check the entry lessons' displayed arithmetic against their source operands."""

import re
from fractions import Fraction
from pathlib import Path

import pytest


CHAPTERS = Path(__file__).resolve().parents[2] / "papers/learning/chapters"


def _zip_exact(*sequences):
    """Pair sequences, refusing a length mismatch.

    The zip strict keyword says this in one word and arrived in 3.10; the
    quality workflow still tests 3.9, where the keyword is a TypeError raised
    at the call rather than a length report.
    """
    lengths = {len(sequence) for sequence in sequences}
    assert len(lengths) == 1, f"length mismatch: {sorted(lengths)}"
    return zip(*sequences)


def _matrix(source: str, name: str) -> list[list[int]]:
    match = re.search(rf"{name}=\\begin\{{pmatrix\}}(.*?)\\end\{{pmatrix\}}", source)
    assert match is not None, f"Missing displayed matrix {name}"
    return [[int(entry) for entry in row.split("&")] for row in match[1].split(r"\\")]


def _apply(matrix: list[list[int]], vector: list[int]) -> list[int]:
    return [
        sum(entry * coordinate for entry, coordinate in _zip_exact(row, vector)) for row in matrix
    ]


def _inner(first: list[complex], second: list[complex]) -> complex:
    return sum(left.conjugate() * right for left, right in _zip_exact(first, second))


def _check_account_example(source: str) -> None:
    account_matrix = _matrix(source, "A")
    assert _apply(account_matrix, [4, 3]) == [11, 10]
    assert r"=\begin{pmatrix}11\\10\end{pmatrix}" in source
    assert [first - second for first, second in _zip_exact(*account_matrix)] == [1, -1]


def test_displayed_account_map_and_composition() -> None:
    source = (CHAPTERS / "matrix_maps.tex").read_text()
    _check_account_example(source)
    first_map = _matrix(source, "C")
    second_map = _matrix(source, "D")
    assert _apply(first_map, _apply(second_map, [1, 2])) == [4, 2]
    assert _apply(second_map, _apply(first_map, [1, 2])) == [6, 2]
    assert r"C(Du)=(4,2)^T" in source
    assert r"D(Cu)=(6,2)^T" in source
    assert _apply(_matrix(source, "M"), [2, 5]) == [11, 12]


def test_account_operand_mutation_is_rejected() -> None:
    source = (CHAPTERS / "matrix_maps.tex").read_text()
    mutated = source.replace(r"A=\begin{pmatrix}2&1", r"A=\begin{pmatrix}3&1", 1)
    assert mutated != source
    with pytest.raises(AssertionError):
        _check_account_example(mutated)


def test_displayed_complex_arithmetic_and_inner_product() -> None:
    source = (CHAPTERS / "complex_numbers.tex").read_text()
    match = re.search(r"For \$z=(\d+)\+i\$ and \$w=(\d+)-(\d+)i\$", source)
    assert match is not None
    first_number = complex(int(match[1]), 1)
    second_number = complex(int(match[2]), -int(match[3]))
    assert first_number * second_number == 5 - 5j
    assert "=5-5i" in source
    assert first_number / second_number == pytest.approx(-0.1 + 0.7j)
    assert r"=-\frac1{10}+\frac7{10}i" in source
    assert r"u=(1,i)^T$ and $v=(i,1)^T" in source
    first_vector = [1 + 0j, 1j]
    second_vector = [1j, 1 + 0j]
    assert _inner(first_vector, second_vector) == 0
    assert _inner(first_vector, first_vector) == 2
    # Omitting conjugation supplies an independent negative control.
    assert sum(coordinate * coordinate for coordinate in first_vector) == 0
    assert Fraction(2, 6) + Fraction(4, 6) == 1
