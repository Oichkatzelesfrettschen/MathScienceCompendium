"""Cayley-Dickson Algebra System Implementation.

This module implements the Cayley-Dickson construction for generating
hypercomplex number systems: R -> C -> H -> O -> S -> ...

The construction recursively doubles dimensions:
- Real numbers (R): 1D
- Complex numbers (C): 2D
- Quaternions (H): 4D
- Octonions (O): 8D
- Sedenions (S): 16D
- Pathions (P): 32D
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

import numpy as np
from typing_extensions import Self

from ..config import Config


if TYPE_CHECKING:
    from pathlib import Path


class _NumpyEncoder(json.JSONEncoder):
    """JSON encoder that converts numpy scalars to Python natives."""

    def default(self, o: Any) -> Any:
        if isinstance(o, np.bool_):
            return bool(o)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        return super().default(o)


def _recursive_cayley_dickson_product(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    """Multiply equal-size coefficient vectors using the repository convention."""
    if left.shape != right.shape or left.ndim != 1:
        raise ValueError("Cayley-Dickson operands must be equal one-dimensional vectors")
    if len(left) == 1:
        return cast("np.ndarray", left * right)
    if len(left) % 2 != 0:
        raise ValueError("Cayley-Dickson coefficient count must be a power of two")

    half_dimension = len(left) // 2
    left_a, left_b = left[:half_dimension], left[half_dimension:]
    right_a, right_b = right[:half_dimension], right[half_dimension:]
    conjugate_right_a = right_a.copy()
    conjugate_right_a[1:] *= -1.0
    conjugate_right_b = right_b.copy()
    conjugate_right_b[1:] *= -1.0
    product_left = _recursive_cayley_dickson_product(
        left_a, right_a
    ) - _recursive_cayley_dickson_product(conjugate_right_b, left_b)
    product_right = _recursive_cayley_dickson_product(
        right_b, left_a
    ) + _recursive_cayley_dickson_product(left_b, conjugate_right_a)
    return cast("np.ndarray", np.concatenate((product_left, product_right)))


@dataclass
class AlgebraicProperties:
    """Properties of a Cayley-Dickson algebra."""

    dimension: int
    is_commutative: bool
    is_associative: bool
    is_alternative: bool
    is_power_associative: bool
    is_flexible: bool
    norm_is_multiplicative: bool
    is_division_algebra: bool
    has_zero_divisors: bool
    name: str

    def to_dict(self) -> dict[str, Any]:
        """Convert properties to dictionary."""
        return {
            "name": self.name,
            "dimension": self.dimension,
            "is_commutative": self.is_commutative,
            "is_associative": self.is_associative,
            "is_alternative": self.is_alternative,
            "is_power_associative": self.is_power_associative,
            "is_flexible": self.is_flexible,
            "norm_is_multiplicative": self.norm_is_multiplicative,
            "is_division_algebra": self.is_division_algebra,
            "has_zero_divisors": self.has_zero_divisors,
        }


class CayleyDickson:
    """Base class for Cayley-Dickson algebras."""

    def __init__(self, coefficients: np.ndarray | list[float] | float) -> None:
        """Initialize a Cayley-Dickson number.

        Args:
            coefficients: Coefficients for basis elements
        """
        if isinstance(coefficients, (int, float)):
            self.coeffs = np.zeros(self._dimension())
            self.coeffs[0] = float(coefficients)
        elif isinstance(coefficients, list):
            self.coeffs = np.zeros(self._dimension())
            for i, c in enumerate(coefficients[: self._dimension()]):
                self.coeffs[i] = float(c)
        else:
            self.coeffs = np.array(coefficients, dtype=np.float64)
            if len(self.coeffs) < self._dimension():
                self.coeffs = np.pad(self.coeffs, (0, self._dimension() - len(self.coeffs)))
            elif len(self.coeffs) > self._dimension():
                self.coeffs = self.coeffs[: self._dimension()]

    def _dimension(self) -> int:
        """Return the dimension of this algebra."""
        raise NotImplementedError

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}({self.coeffs.tolist()})"

    def __str__(self) -> str:
        """Human-readable string."""
        parts = []
        basis_names = self._basis_names()
        for i, coeff in enumerate(self.coeffs):
            if abs(coeff) > 1e-10:
                if i == 0:
                    parts.append(f"{coeff:.4f}")
                else:
                    sign = "+" if coeff >= 0 else "-"
                    if len(parts) > 0:
                        parts.append(f" {sign} {abs(coeff):.4f}{basis_names[i]}")
                    else:
                        parts.append(f"{coeff:.4f}{basis_names[i]}")
        return "".join(parts) if parts else "0"

    def _basis_names(self) -> list[str]:
        """Return basis element names."""
        raise NotImplementedError

    def __add__(self, other: CayleyDickson | float) -> Self:
        """Addition."""
        if isinstance(other, (int, float)):
            result = self.coeffs.copy()
            result[0] += other
            return self.__class__(result)
        elif isinstance(other, self.__class__):
            return self.__class__(self.coeffs + other.coeffs)
        else:
            return NotImplemented

    def __radd__(self, other: CayleyDickson | float) -> Self:
        """Right addition."""
        return self.__add__(other)

    def __sub__(self, other: CayleyDickson | float) -> Self:
        """Subtraction."""
        if isinstance(other, (int, float)):
            result = self.coeffs.copy()
            result[0] -= other
            return self.__class__(result)
        elif isinstance(other, self.__class__):
            return self.__class__(self.coeffs - other.coeffs)
        else:
            raise ArithmeticError(f"Cannot subtract {type(other)} from {type(self)}")

    def __rsub__(self, other: CayleyDickson | float) -> Self:
        """Right subtraction."""
        if isinstance(other, (int, float)):
            result = -self.coeffs
            result[0] += other
            return self.__class__(result)
        else:
            return NotImplemented

    def __neg__(self) -> Self:
        """Negation."""
        return self.__class__(-self.coeffs)

    def __mul__(self, other: CayleyDickson | float) -> Self:
        """Multiplication (must be overridden for each algebra)."""
        raise NotImplementedError

    def __rmul__(self, other: CayleyDickson | float) -> Self:
        """Right multiplication."""
        if isinstance(other, (int, float)):
            return self.__class__(other * self.coeffs)
        else:
            return NotImplemented

    def __truediv__(self, other: CayleyDickson | float) -> Self:
        """Division."""
        if isinstance(other, (int, float)):
            if abs(other) < 1e-10:
                raise ZeroDivisionError("Division by zero")
            return self.__class__(self.coeffs / other)
        elif isinstance(other, self.__class__):
            return self * other.inverse()
        else:
            return NotImplemented

    def conjugate(self) -> Self:
        """Complex conjugate."""
        result = self.coeffs.copy()
        result[1:] *= -1
        return self.__class__(result)

    def norm_squared(self) -> float:
        """Squared norm."""
        return float(np.sum(self.coeffs**2))

    def norm(self) -> float:
        """Euclidean norm."""
        return float(np.sqrt(self.norm_squared()))

    def inverse(self) -> Self:
        """Multiplicative inverse."""
        norm_sq = self.norm_squared()
        if norm_sq < 1e-10:
            raise ZeroDivisionError("Cannot invert zero element")
        return self.conjugate() / norm_sq

    def normalized(self) -> Self:
        """Return normalized version (unit norm)."""
        n = self.norm()
        if n < 1e-10:
            raise ValueError("Cannot normalize zero element")
        return self / n

    @classmethod
    def basis_element(cls, index: int) -> Self:
        """Create a basis element."""
        coeffs = np.zeros(cls._dimension_static())
        coeffs[index] = 1.0
        return cls(coeffs)

    @classmethod
    def _dimension_static(cls) -> int:
        """Static method to get dimension."""
        raise NotImplementedError

    @classmethod
    def random(cls, scale: float = 1.0) -> Self:
        """Create random element."""
        coeffs = np.random.randn(cls._dimension_static()) * scale
        return cls(coeffs)


class Real(CayleyDickson):
    """Real numbers (1D)."""

    def _dimension(self) -> int:
        return 1

    @classmethod
    def _dimension_static(cls) -> int:
        return 1

    def _basis_names(self) -> list[str]:
        return [""]

    def __mul__(self, other: CayleyDickson | float) -> Real:
        """Real multiplication."""
        if isinstance(other, (int, float)):
            return Real(self.coeffs[0] * other)
        elif isinstance(other, Real):
            return Real(self.coeffs[0] * other.coeffs[0])
        else:
            return NotImplemented

    @staticmethod
    def properties() -> AlgebraicProperties:
        """Return algebraic properties."""
        return AlgebraicProperties(
            dimension=1,
            is_commutative=True,
            is_associative=True,
            is_alternative=True,
            is_power_associative=True,
            is_flexible=True,
            norm_is_multiplicative=True,
            is_division_algebra=True,
            has_zero_divisors=False,
            name="Real",
        )


class Complex(CayleyDickson):
    """Complex numbers (2D)."""

    def _dimension(self) -> int:
        return 2

    @classmethod
    def _dimension_static(cls) -> int:
        return 2

    def _basis_names(self) -> list[str]:
        return ["", "i"]

    def __mul__(self, other: CayleyDickson | float) -> Complex:
        """Complex multiplication: (a+bi)(c+di) = (ac-bd) + (ad+bc)i."""
        if isinstance(other, (int, float)):
            return Complex(self.coeffs * other)
        elif isinstance(other, Complex):
            a, b = self.coeffs[0], self.coeffs[1]
            c, d = other.coeffs[0], other.coeffs[1]
            return Complex([a * c - b * d, a * d + b * c])
        else:
            return NotImplemented

    @property
    def real(self) -> float:
        """Real part."""
        return float(self.coeffs[0])

    @property
    def imag(self) -> float:
        """Imaginary part."""
        return float(self.coeffs[1])

    def arg(self) -> float:
        """Argument (phase angle)."""
        return float(np.arctan2(self.imag, self.real))

    @staticmethod
    def properties() -> AlgebraicProperties:
        """Return algebraic properties."""
        return AlgebraicProperties(
            dimension=2,
            is_commutative=True,
            is_associative=True,
            is_alternative=True,
            is_power_associative=True,
            is_flexible=True,
            norm_is_multiplicative=True,
            is_division_algebra=True,
            has_zero_divisors=False,
            name="Complex",
        )


class Quaternion(CayleyDickson):
    """Quaternions (4D) - Hamilton's quaternions."""

    def _dimension(self) -> int:
        return 4

    @classmethod
    def _dimension_static(cls) -> int:
        return 4

    def _basis_names(self) -> list[str]:
        return ["", "i", "j", "k"]

    def __mul__(self, other: CayleyDickson | float) -> Quaternion:
        """Quaternion multiplication using Hamilton's rules:
        i^2 = j^2 = k^2 = ijk = -1
        ij = k, jk = i, ki = j
        ji = -k, kj = -i, ik = -j
        """
        if isinstance(other, (int, float)):
            return Quaternion(self.coeffs * other)
        elif isinstance(other, Quaternion):
            # (a0 + a1i + a2j + a3k)(b0 + b1i + b2j + b3k)  # noqa: ERA001
            a = self.coeffs
            b = other.coeffs
            result = np.zeros(4)

            # Real part: a0*b0 - a1*b1 - a2*b2 - a3*b3
            result[0] = a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3]

            # i component: a0*b1 + a1*b0 + a2*b3 - a3*b2
            result[1] = a[0] * b[1] + a[1] * b[0] + a[2] * b[3] - a[3] * b[2]

            # j component: a0*b2 - a1*b3 + a2*b0 + a3*b1
            result[2] = a[0] * b[2] - a[1] * b[3] + a[2] * b[0] + a[3] * b[1]

            # k component: a0*b3 + a1*b2 - a2*b1 + a3*b0
            result[3] = a[0] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[0]

            return Quaternion(result)
        else:
            return NotImplemented

    @property
    def scalar(self) -> float:
        """Scalar (real) part."""
        return float(self.coeffs[0])

    @property
    def vector(self) -> np.ndarray:
        """Vector (imaginary) part."""
        return cast("np.ndarray", self.coeffs[1:4])

    def to_rotation_matrix(self) -> np.ndarray:
        """Convert unit quaternion to 3x3 rotation matrix."""
        q = self.normalized()
        w, x, y, z = q.coeffs

        return cast(
            "np.ndarray",
            np.asarray(
                [
                    [1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                    [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                    [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)],
                ],
                dtype=np.float64,
            ),
        )

    @classmethod
    def from_axis_angle(cls, axis: np.ndarray, angle: float) -> Quaternion:
        """Create quaternion from axis-angle representation."""
        axis = np.array(axis, dtype=np.float64)
        axis = axis / np.linalg.norm(axis)
        half_angle = angle / 2
        coeffs = np.zeros(4)
        coeffs[0] = np.cos(half_angle)
        coeffs[1:4] = axis * np.sin(half_angle)
        return cls(coeffs)

    @staticmethod
    def properties() -> AlgebraicProperties:
        """Return algebraic properties."""
        return AlgebraicProperties(
            dimension=4,
            is_commutative=False,
            is_associative=True,
            is_alternative=True,
            is_power_associative=True,
            is_flexible=True,
            norm_is_multiplicative=True,
            is_division_algebra=True,
            has_zero_divisors=False,
            name="Quaternion",
        )


class Octonion(CayleyDickson):
    """Octonions (8D) - Cayley's octonions."""

    def _dimension(self) -> int:
        return 8

    @classmethod
    def _dimension_static(cls) -> int:
        return 8

    def _basis_names(self) -> list[str]:
        return ["", "e1", "e2", "e3", "e4", "e5", "e6", "e7"]

    def __mul__(self, other: CayleyDickson | float) -> Octonion:
        """Octonion multiplication using Cayley-Dickson construction."""
        if isinstance(other, (int, float)):
            return Octonion(self.coeffs * other)
        elif isinstance(other, Octonion):
            # Split into quaternion pairs: o = a + b*e4
            a_coeffs = self.coeffs[:4]
            b_coeffs = self.coeffs[4:]
            c_coeffs = other.coeffs[:4]
            d_coeffs = other.coeffs[4:]

            # Convert to quaternions for computation
            a = Quaternion(a_coeffs)
            b = Quaternion(b_coeffs)
            c = Quaternion(c_coeffs)
            d = Quaternion(d_coeffs)

            # Cayley-Dickson formula: (a,b)(c,d) = (ac - d*b, da + bc*)
            # where * denotes conjugation and multiplication order matters
            result_left = (a * c - Quaternion(d.conjugate().coeffs) * b).coeffs
            result_right = (d * a + b * Quaternion(c.conjugate().coeffs)).coeffs

            result = np.zeros(8)
            result[:4] = result_left
            result[4:] = result_right

            return Octonion(result)
        else:
            return NotImplemented

    def associator(self, y: Octonion, z: Octonion) -> Octonion:
        """Associator [x,y,z] = (xy)z - x(yz)."""
        return (self * y) * z - self * (y * z)

    def is_zero_divisor(self) -> bool:
        """Check if this element is a zero divisor."""
        # In octonions, only zero is a zero divisor
        return self.norm_squared() < 1e-10

    @staticmethod
    def properties() -> AlgebraicProperties:
        """Return algebraic properties."""
        return AlgebraicProperties(
            dimension=8,
            is_commutative=False,
            is_associative=False,
            is_alternative=True,  # Octonions are alternative
            is_power_associative=True,
            is_flexible=True,
            norm_is_multiplicative=True,
            is_division_algebra=True,
            has_zero_divisors=False,
            name="Octonion",
        )

    @staticmethod
    def multiplication_table() -> np.ndarray:
        """Generate the multiplication table for octonion basis elements."""
        # Fano plane-based multiplication table
        table = np.array(
            [
                [1, 2, 3, 4, 5, 6, 7, 8],  # e0 (identity)
                [2, -1, 4, -3, 6, -5, -8, 7],  # e1
                [3, -4, -1, 2, 7, 8, -5, -6],  # e2
                [4, 3, -2, -1, 8, -7, 6, -5],  # e3
                [5, -6, -7, -8, -1, 2, 3, 4],  # e4
                [6, 5, -8, 7, -2, -1, -4, 3],  # e5
                [7, 8, 5, -6, -3, 4, -1, -2],  # e6
                [8, -7, 6, 5, -4, -3, 2, -1],  # e7
            ]
        )
        return cast("np.ndarray", table)


class Sedenion(CayleyDickson):
    """Sedenions (16D) - 16-dimensional hypercomplex numbers."""

    def _dimension(self) -> int:
        return 16

    @classmethod
    def _dimension_static(cls) -> int:
        return 16

    def _basis_names(self) -> list[str]:
        names = [""]
        for i in range(1, 16):
            names.append(f"e{i}")
        return names

    def __mul__(self, other: CayleyDickson | float) -> Sedenion:
        """Sedenion multiplication using Cayley-Dickson construction."""
        if isinstance(other, (int, float)):
            return Sedenion(self.coeffs * other)
        elif isinstance(other, Sedenion):
            # Split into octonion pairs: s = a + b*e8
            a_coeffs = self.coeffs[:8]
            b_coeffs = self.coeffs[8:]
            c_coeffs = other.coeffs[:8]
            d_coeffs = other.coeffs[8:]

            # Use Cayley-Dickson construction with octonions
            # (a,b)(c,d) = (ac - d*b, da + bc*)
            a = Octonion(a_coeffs)
            b = Octonion(b_coeffs)
            c = Octonion(c_coeffs)
            d = Octonion(d_coeffs)

            result_left = (a * c - Octonion(d.conjugate().coeffs) * b).coeffs
            result_right = (d * a + b * Octonion(c.conjugate().coeffs)).coeffs

            result = np.zeros(16)
            result[:8] = result_left
            result[8:] = result_right

            return Sedenion(result)
        else:
            return NotImplemented

    def has_zero_divisor_with(self, other: Sedenion) -> bool:
        """Check if multiplication with other gives zero despite both being non-zero."""
        if self.norm_squared() < 1e-10 or other.norm_squared() < 1e-10:
            return False  # One is already zero
        product = self * other
        return product.norm_squared() < 1e-10

    @staticmethod
    def find_zero_divisors(trials: int = 100) -> list[tuple[Sedenion, Sedenion]]:
        """Return a deterministic exact zero-divisor witness when requested."""
        if trials <= 0:
            return []
        left_factor = Sedenion.basis_element(3) + Sedenion.basis_element(10)
        right_factor = Sedenion.basis_element(6) - Sedenion.basis_element(15)
        if not left_factor.has_zero_divisor_with(right_factor):
            raise ArithmeticError("canonical sedenion zero-divisor witness failed")
        return [(left_factor, right_factor)]

    @staticmethod
    def properties() -> AlgebraicProperties:
        """Return algebraic properties."""
        return AlgebraicProperties(
            dimension=16,
            is_commutative=False,
            is_associative=False,
            is_alternative=False,  # Lost at sedenions
            is_power_associative=True,
            is_flexible=True,
            norm_is_multiplicative=False,
            is_division_algebra=False,  # Has zero divisors
            has_zero_divisors=True,
            name="Sedenion",
        )


class Pathion(CayleyDickson):
    """Pathions (32D) - 32-dimensional hypercomplex numbers."""

    def _dimension(self) -> int:
        return 32

    @classmethod
    def _dimension_static(cls) -> int:
        return 32

    def _basis_names(self) -> list[str]:
        names = [""]
        for i in range(1, 32):
            names.append(f"f{i}")
        return names

    def __mul__(self, other: CayleyDickson | float) -> Pathion:
        """Pathion multiplication using Cayley-Dickson construction."""
        if isinstance(other, (int, float)):
            return Pathion(self.coeffs * other)
        elif isinstance(other, Pathion):
            # Split into sedenion pairs
            a_coeffs = self.coeffs[:16]
            b_coeffs = self.coeffs[16:]
            c_coeffs = other.coeffs[:16]
            d_coeffs = other.coeffs[16:]

            a = Sedenion(a_coeffs)
            b = Sedenion(b_coeffs)
            c = Sedenion(c_coeffs)
            d = Sedenion(d_coeffs)

            result_left = (a * c - Sedenion(d.conjugate().coeffs) * b).coeffs
            result_right = (d * a + b * Sedenion(c.conjugate().coeffs)).coeffs

            result = np.zeros(32)
            result[:16] = result_left
            result[16:] = result_right

            return Pathion(result)
        else:
            return NotImplemented

    @staticmethod
    def properties() -> AlgebraicProperties:
        """Return algebraic properties."""
        return AlgebraicProperties(
            dimension=32,
            is_commutative=False,
            is_associative=False,
            is_alternative=False,
            is_power_associative=True,
            is_flexible=True,
            norm_is_multiplicative=False,
            is_division_algebra=False,
            has_zero_divisors=True,
            name="Pathion",
        )


class Chingon(Pathion):
    """256-dimensional Cayley-Dickson algebra."""

    @classmethod
    def _dimension_static(cls) -> int:
        return 256

    def _dimension(self) -> int:
        return self._dimension_static()

    def __mul__(self, other: CayleyDickson | float) -> Self:
        if isinstance(other, (int, float)):
            return self.__class__(self.coeffs * other)
        if isinstance(other, self.__class__):
            return self.__class__(_recursive_cayley_dickson_product(self.coeffs, other.coeffs))
        return NotImplemented

    @classmethod
    def _basis_names(cls) -> list[str]:
        return ["e" + str(i) for i in range(256)]


class Rouxion(Chingon):
    """512-dimensional Cayley-Dickson algebra."""

    @classmethod
    def _dimension_static(cls) -> int:
        return 512

    @classmethod
    def _basis_names(cls) -> list[str]:
        return ["e" + str(i) for i in range(512)]


class Polyxon(Rouxion):
    """1024-dimensional Cayley-Dickson algebra."""

    @classmethod
    def _dimension_static(cls) -> int:
        return 1024

    @classmethod
    def _basis_names(cls) -> list[str]:
        return ["e" + str(i) for i in range(1024)]


class CayleyDicksonValidator:
    """Validator for Cayley-Dickson algebra properties."""

    def __init__(self, algebra_class: type[CayleyDickson]) -> None:
        """Initialize validator with an algebra class."""
        self.algebra_class = algebra_class
        self.dimension = algebra_class._dimension_static()
        self.name = algebra_class.__name__

    def verify_multiplication_closure(self, trials: int = 100) -> bool:
        """Verify that multiplication is closed."""
        for _ in range(trials):
            a = self.algebra_class.random()
            b = self.algebra_class.random()
            c = a * b
            if not isinstance(c, self.algebra_class):
                return False
        return True

    def verify_associativity(
        self, trials: int = 100, tolerance: float = 1e-10
    ) -> tuple[bool, float]:
        """Verify associativity: (ab)c = a(bc)."""
        max_error = 0.0
        for _ in range(trials):
            a = self.algebra_class.random()
            b = self.algebra_class.random()
            c = self.algebra_class.random()

            left = (a * b) * c
            right = a * (b * c)

            error = float(np.linalg.norm(left.coeffs - right.coeffs))
            max_error = max(max_error, error)

        return max_error < tolerance, max_error

    def verify_commutativity(
        self, trials: int = 100, tolerance: float = 1e-10
    ) -> tuple[bool, float]:
        """Verify commutativity: ab = ba."""
        max_error = 0.0
        for _ in range(trials):
            a = self.algebra_class.random()
            b = self.algebra_class.random()

            left = a * b
            right = b * a

            error = float(np.linalg.norm(left.coeffs - right.coeffs))
            max_error = max(max_error, error)

        return max_error < tolerance, max_error

    def verify_alternativity(
        self, trials: int = 100, tolerance: float = 1e-10
    ) -> tuple[bool, float]:
        """Verify alternativity: (aa)b = a(ab) and (ab)b = a(bb)."""
        max_error = 0.0
        for _ in range(trials):
            a = self.algebra_class.random()
            b = self.algebra_class.random()

            # Left alternativity: (aa)b = a(ab)
            left1 = (a * a) * b
            right1 = a * (a * b)
            error1 = float(np.linalg.norm(left1.coeffs - right1.coeffs))

            # Right alternativity: (ab)b = a(bb)
            left2 = (a * b) * b
            right2 = a * (b * b)
            error2 = float(np.linalg.norm(left2.coeffs - right2.coeffs))

            max_error = max(max_error, error1, error2)

        return max_error < tolerance, max_error

    def verify_norm_multiplicativity(
        self, trials: int = 100, tolerance: float = 1e-10
    ) -> tuple[bool, float]:
        """Verify norm multiplicativity: |ab| = |a||b|."""
        max_relative_error = 0.0
        for _ in range(trials):
            a = self.algebra_class.random()
            b = self.algebra_class.random()

            norm_product = (a * b).norm()
            product_norms = a.norm() * b.norm()

            if product_norms > tolerance:
                relative_error = abs(norm_product - product_norms) / product_norms
                max_relative_error = max(max_relative_error, relative_error)

        return max_relative_error < tolerance, max_relative_error

    def find_zero_divisors(self, trials: int = 1000) -> list[tuple[CayleyDickson, CayleyDickson]]:
        """Return the canonical embedded sedenion zero-divisor witness."""
        zero_divisors: list[tuple[CayleyDickson, CayleyDickson]] = []

        if self.dimension <= 8 or trials <= 0:
            return zero_divisors

        left_factor = self.algebra_class.basis_element(3) + self.algebra_class.basis_element(10)
        right_factor = self.algebra_class.basis_element(6) - self.algebra_class.basis_element(15)
        if (
            left_factor.norm_squared() > 0.0
            and right_factor.norm_squared() > 0.0
            and (left_factor * right_factor).norm_squared() == 0.0
        ):
            zero_divisors.append((left_factor, right_factor))
        return zero_divisors

    def generate_multiplication_table(self) -> np.ndarray:
        """Generate multiplication table for basis elements."""
        n = self.dimension
        table = np.zeros((n, n, n))

        for i in range(n):
            for j in range(n):
                ei = self.algebra_class.basis_element(i)
                ej = self.algebra_class.basis_element(j)
                product = ei * ej
                table[i, j, :] = product.coeffs

        return cast("np.ndarray", table)

    def verify_all_properties(self) -> dict[str, Any]:
        """Run all verification tests."""
        print(f"\nVerifying properties of {self.name} (dimension {self.dimension})")
        print("=" * 60)

        results = {"algebra": self.name, "dimension": self.dimension}

        # Closure
        print("Testing closure...", end=" ")
        results["closure"] = self.verify_multiplication_closure()
        print("PASS" if results["closure"] else "FAIL")

        # Associativity
        print("Testing associativity...", end=" ")
        is_assoc, assoc_error = self.verify_associativity()
        results["associative"] = is_assoc
        results["associativity_error"] = assoc_error
        print(f"{'PASS' if is_assoc else 'FAIL'} (max error: {assoc_error:.2e})")

        # Commutativity
        print("Testing commutativity...", end=" ")
        is_comm, comm_error = self.verify_commutativity()
        results["commutative"] = is_comm
        results["commutativity_error"] = comm_error
        print(f"{'PASS' if is_comm else 'FAIL'} (max error: {comm_error:.2e})")

        # Alternativity
        print("Testing alternativity...", end=" ")
        is_alt, alt_error = self.verify_alternativity()
        results["alternative"] = is_alt
        results["alternativity_error"] = alt_error
        print(f"{'PASS' if is_alt else 'FAIL'} (max error: {alt_error:.2e})")

        # Norm multiplicativity
        print("Testing norm multiplicativity...", end=" ")
        norm_mult, norm_error = self.verify_norm_multiplicativity()
        results["norm_multiplicative"] = norm_mult
        results["norm_error"] = norm_error
        print(f"{'PASS' if norm_mult else 'FAIL'} (max error: {norm_error:.2e})")

        # Zero divisors
        print("Searching for zero divisors...", end=" ")
        zero_divs = self.find_zero_divisors()
        results["has_zero_divisors"] = len(zero_divs) > 0
        results["zero_divisor_count"] = len(zero_divs)
        print(f"Found {len(zero_divs)}")

        return results


def run_comprehensive_validation(output_dir: Path | None = None) -> dict[str, Any]:
    """Run validation on all implemented algebras."""
    if output_dir is None:
        output_dir = Config.RESULTS_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    algebras = [
        (Real, "Real"),
        (Complex, "Complex"),
        (Quaternion, "Quaternion"),
        (Octonion, "Octonion"),
        (Sedenion, "Sedenion"),
        (Pathion, "Pathion"),
    ]

    all_results = {}

    for algebra_class, name in algebras:
        validator = CayleyDicksonValidator(algebra_class)
        results = validator.verify_all_properties()
        all_results[name] = results

        # Save individual results
        with (output_dir / f"cayley_dickson_{name.lower()}_validation.json").open("w") as f:
            json.dump(results, f, indent=2, cls=_NumpyEncoder)

    # Save combined results
    with (output_dir / "cayley_dickson_all_validation.json").open("w") as f:
        json.dump(all_results, f, indent=2, cls=_NumpyEncoder)

    # Create summary table
    print("\n" + "=" * 80)
    print("SUMMARY OF CAYLEY-DICKSON ALGEBRA PROPERTIES")
    print("=" * 80)
    print(
        f"{'Algebra':<12} {'Dim':<4} {'Comm':<5} {'Assoc':<6} {'Alt':<4} {'Div':<4} {'Zero Div':<8}"
    )
    print("-" * 80)

    for name in ["Real", "Complex", "Quaternion", "Octonion", "Sedenion", "Pathion"]:
        r = all_results[name]
        print(
            f"{name:<12} {r['dimension']:<4} "
            f"{'Y' if r.get('commutative', False) else 'N':<5} "
            f"{'Y' if r.get('associative', False) else 'N':<6} "
            f"{'Y' if r.get('alternative', False) else 'N':<4} "
            f"{'Y' if r.get('norm_multiplicative', False) else 'N':<4} "
            f"{'Y' if r.get('has_zero_divisors', False) else 'N':<8}"
        )

    return all_results


def analyze_algebra_properties(output_dir: Path | None = None) -> dict[str, Any]:
    """Production entry point for analyzing algebra properties."""
    return run_comprehensive_validation(output_dir)


def demonstrate_examples():
    """Demonstrate usage of Cayley-Dickson algebras."""
    print("\n" + "=" * 80)
    print("CAYLEY-DICKSON ALGEBRA DEMONSTRATIONS")
    print("=" * 80)

    # Complex numbers
    print("\n--- Complex Numbers ---")
    z1 = Complex([1, 2])  # 1 + 2i
    z2 = Complex([3, -1])  # 3 - i
    print(f"z1 = {z1}")
    print(f"z2 = {z2}")
    print(f"z1 + z2 = {z1 + z2}")
    print(f"z1 * z2 = {z1 * z2}")
    print(f"|z1| = {z1.norm():.4f}")
    print(f"z1* = {z1.conjugate()}")

    # Quaternions
    print("\n--- Quaternions ---")
    q1 = Quaternion([1, 0.5, 0.5, 0.5])
    q2 = Quaternion([0, 1, 0, 0])
    print(f"q1 = {q1}")
    print(f"q2 = {q2}")
    print(f"q1 * q2 = {q1 * q2}")
    print(f"q2 * q1 = {q2 * q1}")
    print(f"q1 * q2 - q2 * q1 = {q1 * q2 - q2 * q1} (non-commutative)")

    # Rotation quaternion
    axis = np.array([0, 0, 1])  # z-axis
    angle = np.pi / 4  # 45 degrees
    q_rot = Quaternion.from_axis_angle(axis, angle)
    print(f"\nRotation quaternion (45 deg around z): {q_rot}")

    # Octonions
    print("\n--- Octonions ---")
    o1 = Octonion([1, 1, 0, 0, 0, 0, 0, 0])
    o2 = Octonion([0, 0, 1, 0, 0, 0, 0, 0])
    o3 = Octonion([0, 0, 0, 1, 0, 0, 0, 0])
    print(f"o1 = {o1}")
    print(f"o2 = {o2}")
    print(f"o3 = {o3}")
    assoc = o1.associator(o2, o3)
    print(f"[o1, o2, o3] = {assoc} (non-associative)")
    print(f"|[o1, o2, o3]| = {assoc.norm():.4f}")

    # Sedenions and zero divisors
    print("\n--- Sedenions and Zero Divisors ---")
    s1 = Sedenion.basis_element(9) + Sedenion.basis_element(10)
    s2 = Sedenion.basis_element(11) - Sedenion.basis_element(12)
    product = s1 * s2
    print(f"s1 = e9 + e10, |s1| = {s1.norm():.4f}")
    print(f"s2 = e11 - e12, |s2| = {s2.norm():.4f}")
    print(f"s1 * s2 norm = {product.norm():.10f}")
    if product.norm() < 1e-10:
        print("Found zero divisors!")


if __name__ == "__main__":
    # Run demonstrations
    demonstrate_examples()

    # Run comprehensive validation
    results = run_comprehensive_validation()

    print("\nValidation complete. Results saved to experiments/results/")
