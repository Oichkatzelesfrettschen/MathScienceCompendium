"""Fractal Dimension and Geometric Complexity Analytics.

Implements box-counting, Hausdorff measure estimators, and generator
logic for classic and physical fractal systems.
"""

from __future__ import annotations
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
from scipy.spatial.distance import cdist
from scipy.stats import linregress
import json
from pathlib import Path
from dataclasses import dataclass
from .config import Config

# Optional numba for performance
try:
    from numba import jit, prange
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    # Define dummy decorators
    def jit(func=None, **kwargs):
        if func is None:
            return lambda f: f
        return func
    prange = range



@dataclass
class FractalDimensionResult:
    """Results from fractal dimension calculation."""

    method: str
    dimension: float
    error: float
    r_squared: float
    scales: np.ndarray
    measures: np.ndarray
    confidence_interval: Tuple[float, float]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "method": self.method,
            "dimension": float(self.dimension),
            "error": float(self.error),
            "r_squared": float(self.r_squared),
            "scales": self.scales.tolist(),
            "measures": self.measures.tolist(),
            "confidence_interval": list(self.confidence_interval),
            "metadata": self.metadata
        }


class FractalGenerator:
    """Generator for various fractal patterns."""

    @staticmethod
    @jit(nopython=True)
    def mandelbrot_point(c_real: float, c_imag: float, max_iter: int = 100) -> int:
        """Check if a point is in the Mandelbrot set."""
        z_real, z_imag = 0.0, 0.0
        for n in range(max_iter):
            z_real_new = z_real * z_real - z_imag * z_imag + c_real
            z_imag = 2 * z_real * z_imag + c_imag
            z_real = z_real_new

            if z_real * z_real + z_imag * z_imag > 4:
                return n
        return max_iter

    @staticmethod
    def mandelbrot_set(xmin: float = -2.5, xmax: float = 1.5,
                       ymin: float = -2.0, ymax: float = 2.0,
                       width: int = 800, height: int = 600,
                       max_iter: int = 100) -> np.ndarray:
        """Generate the Mandelbrot set."""
        x = np.linspace(xmin, xmax, width)
        y = np.linspace(ymin, ymax, height)
        X, Y = np.meshgrid(x, y)

        # Use vectorized computation
        mandelbrot = np.zeros((height, width), dtype=np.int32)
        for i in prange(height):
            for j in range(width):
                mandelbrot[i, j] = FractalGenerator.mandelbrot_point(
                    X[i, j], Y[i, j], max_iter
                )

        return mandelbrot

    @staticmethod
    def mandelbrot_boundary(xmin: float = -2.5, xmax: float = 1.5,
                           ymin: float = -2.0, ymax: float = 2.0,
                           resolution: int = 1000,
                           max_iter: int = 100,
                           threshold: int = 50) -> np.ndarray:
        """Extract boundary points of the Mandelbrot set."""
        x = np.linspace(xmin, xmax, resolution)
        y = np.linspace(ymin, ymax, resolution)
        boundary_points = []

        for i in range(resolution):
            for j in range(resolution):
                # Check if point is near boundary
                center_val = FractalGenerator.mandelbrot_point(x[i], y[j], max_iter)

                if threshold < center_val < max_iter:
                    # Check neighbors
                    is_boundary = False
                    for di in [-1, 0, 1]:
                        for dj in [-1, 0, 1]:
                            if di == 0 and dj == 0:
                                continue
                            if 0 <= i + di < resolution and 0 <= j + dj < resolution:
                                neighbor_val = FractalGenerator.mandelbrot_point(
                                    x[i + di], y[j + dj], max_iter
                                )
                                if neighbor_val == max_iter or neighbor_val < threshold:
                                    is_boundary = True
                                    break
                        if is_boundary:
                            break

                    if is_boundary:
                        boundary_points.append([x[i], y[j]])

        return np.array(boundary_points)

    @staticmethod
    @jit(nopython=True)
    def julia_point(z_real: float, z_imag: float,
                   c_real: float, c_imag: float, max_iter: int = 100) -> int:
        """Check if a point escapes for Julia set."""
        for n in range(max_iter):
            z_real_new = z_real * z_real - z_imag * z_imag + c_real
            z_imag = 2 * z_real * z_imag + c_imag
            z_real = z_real_new

            if z_real * z_real + z_imag * z_imag > 4:
                return n
        return max_iter

    @staticmethod
    def julia_set(c_real: float = -0.7, c_imag: float = 0.27015,
                 xmin: float = -2.0, xmax: float = 2.0,
                 ymin: float = -1.5, ymax: float = 1.5,
                 width: int = 800, height: int = 600,
                 max_iter: int = 100) -> np.ndarray:
        """Generate a Julia set for given c parameter."""
        x = np.linspace(xmin, xmax, width)
        y = np.linspace(ymin, ymax, height)
        X, Y = np.meshgrid(x, y)

        julia = np.zeros((height, width), dtype=np.int32)
        for i in prange(height):
            for j in range(width):
                julia[i, j] = FractalGenerator.julia_point(
                    X[i, j], Y[i, j], c_real, c_imag, max_iter
                )

        return julia

    @staticmethod
    def sierpinski_triangle(iterations: int = 8, size: int = 512) -> np.ndarray:
        """Generate Sierpinski triangle using chaos game."""
        # Triangle vertices
        vertices = np.array([[0, 0], [size-1, 0], [size//2, int(size*np.sqrt(3)/2)]])

        # Start from random point
        point = np.array([size//2, size//3], dtype=np.float64)

        # Generate points
        points = []
        for _ in range(10000 * iterations):
            # Choose random vertex
            vertex = vertices[np.random.randint(3)]
            # Move halfway to vertex
            point = (point + vertex) / 2
            points.append(point.copy())

        # Convert to image
        image = np.zeros((size, size))
        for p in points[100:]:  # Skip initial points
            x, y = int(p[0]), int(p[1])
            if 0 <= x < size and 0 <= y < size:
                image[y, x] = 1

        return image

    @staticmethod
    def cantor_set(iterations: int = 7) -> List[Tuple[float, float]]:
        """Generate Cantor set intervals."""
        intervals = [(0.0, 1.0)]

        for _ in range(iterations):
            new_intervals = []
            for start, end in intervals:
                third = (end - start) / 3
                new_intervals.append((start, start + third))
                new_intervals.append((end - third, end))
            intervals = new_intervals

        return intervals

    @staticmethod
    def koch_snowflake(iterations: int = 5) -> np.ndarray:
        """Generate Koch snowflake vertices."""

        def koch_segment(p1: np.ndarray, p2: np.ndarray, depth: int) -> List[np.ndarray]:
            """Recursively generate Koch curve segment."""
            if depth == 0:
                return [p1, p2]

            # Divide segment into thirds
            third = (p2 - p1) / 3
            a = p1 + third
            b = p1 + 2 * third

            # Calculate peak point (equilateral triangle)
            angle = np.pi / 3  # 60 degrees
            cos_a = np.cos(angle)
            sin_a = np.sin(angle)
            rotation = np.array([[cos_a, -sin_a], [sin_a, cos_a]])
            peak = a + rotation @ third

            # Recursive calls
            points = []
            points.extend(koch_segment(p1, a, depth - 1)[:-1])
            points.extend(koch_segment(a, peak, depth - 1)[:-1])
            points.extend(koch_segment(peak, b, depth - 1)[:-1])
            points.extend(koch_segment(b, p2, depth - 1))

            return points

        # Start with equilateral triangle
        p1 = np.array([0.0, 0.0])
        p2 = np.array([1.0, 0.0])
        p3 = np.array([0.5, np.sqrt(3) / 2])

        # Generate each side
        side1 = koch_segment(p1, p2, iterations)[:-1]
        side2 = koch_segment(p2, p3, iterations)[:-1]
        side3 = koch_segment(p3, p1, iterations)[:-1]

        # Combine all points
        all_points = side1 + side2 + side3

        return np.array(all_points)

    @staticmethod
    def lorenz_attractor(num_points: int = 10000,
                        sigma: float = 10.0,
                        rho: float = 28.0,
                        beta: float = 8.0/3.0,
                        dt: float = 0.01) -> np.ndarray:
        """Generate points on the Lorenz attractor."""
        # Initial conditions
        x, y, z = 1.0, 1.0, 1.0
        
        # Transient phase
        for _ in range(1000):
            dx = sigma * (y - x)
            dy = x * (rho - z) - y
            dz = x * y - beta * z
            x += dx * dt
            y += dy * dt
            z += dz * dt

        points = []
        for _ in range(num_points):
            # Lorenz equations
            dx = sigma * (y - x)
            dy = x * (rho - z) - y
            dz = x * y - beta * z

            # Euler integration
            x += dx * dt
            y += dy * dt
            z += dz * dt

            points.append([x, y, z])

        return np.array(points)

    @staticmethod
    def henon_map(num_points: int = 10000,
                  a: float = 1.4, b: float = 0.3) -> np.ndarray:
        """Generate points from the Henon map."""
        x, y = 0.1, 0.1
        
        # Transient
        for _ in range(100):
            x_new = 1 - a * x * x + y
            y_new = b * x
            x, y = x_new, y_new

        points = []
        for _ in range(num_points):
            x_new = 1 - a * x * x + y
            y_new = b * x
            x, y = x_new, y_new
            points.append([x, y])

        return np.array(points)


class FractalDimensionCalculator:
    """Calculate fractal dimensions using various methods."""

    @staticmethod
    def box_counting_dimension(points: np.ndarray,
                              min_scale: Optional[float] = None,
                              max_scale: Optional[float] = None,
                              num_scales: int = 20) -> FractalDimensionResult:
        """Calculate box-counting (Minkowski-Bouligand) dimension."""
        if len(points) == 0:
            raise ValueError("No points provided")

        points = np.array(points)
        
        # Normalize data to [0, 1] unit hypercube
        mins = points.min(axis=0)
        maxs = points.max(axis=0)
        ranges = maxs - mins
        ranges[ranges < 1e-10] = 1.0
        normalized = (points - mins) / ranges

        # Determine scale range - more robust for small datasets
        if min_scale is None:
            min_scale = 2.0 / len(points)
        if max_scale is None:
            max_scale = 0.5

        scales = np.logspace(np.log10(min_scale), np.log10(max_scale), num_scales)
        counts = []

        for scale in scales:
            # Vectorized box counting
            # Shift by epsilon to avoid edge cases
            eps = 1e-10
            bins = np.floor((normalized + eps) / scale).astype(int)
            # Find unique bins (boxes) occupied
            unique_bins = np.unique(bins, axis=0)
            counts.append(len(unique_bins))

        counts = np.array(counts)
        log_inv_scales = np.log(1.0 / scales)
        log_counts = np.log(counts)

        # Linear regression on log-log plot
        slope, intercept, r_value, p_value, std_err = linregress(log_inv_scales, log_counts)
        dimension = slope

        confidence = 1.96 * std_err
        confidence_interval = (dimension - confidence, dimension + confidence)

        return FractalDimensionResult(
            method="box_counting",
            dimension=dimension,
            error=std_err,
            r_squared=r_value ** 2,
            scales=scales,
            measures=counts,
            confidence_interval=confidence_interval,
            metadata={
                "num_points": len(points),
                "num_scales": num_scales,
                "p_value": p_value
            }
        )

    @staticmethod
    def hausdorff_dimension(points: np.ndarray,
                           min_scale: Optional[float] = None,
                           max_scale: Optional[float] = None,
                           num_scales: int = 20,
                           method: str = "covering") -> FractalDimensionResult:
        """Estimate Hausdorff dimension using covering method."""
        if len(points) == 0:
            raise ValueError("No points provided")

        points = np.array(points)

        # Normalize points
        mins = np.min(points, axis=0)
        maxs = np.max(points, axis=0)
        ranges = maxs - mins
        ranges[ranges < 1e-10] = 1.0
        normalized = (points - mins) / ranges

        # Determine scale range
        if min_scale is None:
            min_scale = 1e-4
        if max_scale is None:
            max_scale = 0.1

        scales = np.logspace(np.log10(min_scale), np.log10(max_scale), num_scales)
        measures = []

        for radius in scales:
            if method == "covering":
                # Estimate minimum covering
                covered = np.zeros(len(normalized), dtype=bool)
                num_balls = 0

                while not np.all(covered):
                    # Find uncovered point
                    uncovered_idx = np.where(~covered)[0][0]
                    center = normalized[uncovered_idx]

                    # Find all points within radius
                    distances = np.linalg.norm(normalized - center, axis=1)
                    covered |= (distances <= radius)
                    num_balls += 1

                    # Prevent infinite loop
                    if num_balls > len(points):
                        break

                measures.append(num_balls)

            elif method == "packing":
                # Maximum packing
                packed = []
                available = list(range(len(normalized)))

                while available:
                    # Choose random point
                    idx = available.pop(np.random.randint(len(available)))
                    center = normalized[idx]
                    packed.append(center)

                    # Remove points too close
                    new_available = []
                    for i in available:
                        if np.linalg.norm(normalized[i] - center) > 2 * radius:
                            new_available.append(i)
                    available = new_available

                measures.append(len(packed))

        measures = np.array(measures)

        # Calculate dimension from scaling
        log_scales = np.log(scales)
        log_measures = np.log(measures)

        valid = np.isfinite(log_scales) & np.isfinite(log_measures)
        log_scales = log_scales[valid]
        log_measures = log_measures[valid]

        if len(log_scales) < 3:
            raise ValueError("Insufficient valid data points")

        slope, intercept, r_value, p_value, std_err = linregress(log_scales, log_measures)
        dimension = -slope

        confidence = 1.96 * std_err
        confidence_interval = (dimension - confidence, dimension + confidence)

        return FractalDimensionResult(
            method=f"hausdorff_{method}",
            dimension=dimension,
            error=std_err,
            r_squared=r_value ** 2,
            scales=scales[valid],
            measures=measures[valid],
            confidence_interval=confidence_interval,
            metadata={
                "num_points": len(points),
                "method": method,
                "p_value": p_value
            }
        )

    @staticmethod
    def correlation_dimension(points: np.ndarray,
                            min_scale: Optional[float] = None,
                            max_scale: Optional[float] = None,
                            num_scales: int = 20,
                            sample_size: Optional[int] = None) -> FractalDimensionResult:
        """Calculate correlation dimension."""
        points = np.array(points)
        n_points = len(points)

        if n_points < 10:
            raise ValueError("Need at least 10 points for correlation dimension")

        # Sample points if too many
        if sample_size and n_points > sample_size:
            indices = np.random.choice(n_points, sample_size, replace=False)
            points = points[indices]
            n_points = sample_size

        # Normalize
        mins = np.min(points, axis=0)
        maxs = np.max(points, axis=0)
        ranges = maxs - mins
        ranges[ranges < 1e-10] = 1.0
        normalized = (points - mins) / ranges

        # Compute pairwise distances
        distances = cdist(normalized, normalized)
        np.fill_diagonal(distances, np.inf)  # Exclude self-distances

        # Determine scale range
        min_dist = np.min(distances[distances > 0])
        max_dist = np.max(distances[distances < np.inf])

        if min_scale is None:
            min_scale = min_dist * 2
        if max_scale is None:
            max_scale = max_dist / 2

        scales = np.logspace(np.log10(min_scale), np.log10(max_scale), num_scales)
        correlations = []

        for radius in scales:
            # Count pairs within radius
            count = np.sum(distances < radius)
            # Correlation integral
            C_r = count / (n_points * (n_points - 1))
            correlations.append(C_r)

        correlations = np.array(correlations)

        # Find scaling region
        valid = (correlations > 0) & (correlations < 1)
        if np.sum(valid) < 3:
            raise ValueError("Insufficient valid correlation values")

        log_scales = np.log(scales[valid])
        log_corr = np.log(correlations[valid])

        slope, intercept, r_value, p_value, std_err = linregress(log_scales, log_corr)
        dimension = slope

        confidence = 1.96 * std_err
        confidence_interval = (dimension - confidence, dimension + confidence)

        return FractalDimensionResult(
            method="correlation",
            dimension=dimension,
            error=std_err,
            r_squared=r_value ** 2,
            scales=scales[valid],
            measures=correlations[valid],
            confidence_interval=confidence_interval,
            metadata={
                "num_points": n_points,
                "min_distance": float(min_dist),
                "max_distance": float(max_dist),
                "p_value": p_value
            }
        )

    @staticmethod
    def information_dimension(points: np.ndarray,
                            min_scale: Optional[float] = None,
                            max_scale: Optional[float] = None,
                            num_scales: int = 15) -> FractalDimensionResult:
        """Calculate information dimension."""
        points = np.array(points)

        # Normalize
        mins = np.min(points, axis=0)
        maxs = np.max(points, axis=0)
        ranges = maxs - mins
        ranges[ranges < 1e-10] = 1.0
        normalized = (points - mins) / ranges

        if min_scale is None:
            min_scale = 0.01
        if max_scale is None:
            max_scale = 0.5

        scales = np.logspace(np.log10(min_scale), np.log10(max_scale), num_scales)
        information = []

        for scale in scales:
            grid_size = int(np.ceil(1.0 / scale))

            # Discretize points
            grid_points = (normalized / scale).astype(np.int32)
            grid_points = np.clip(grid_points, 0, grid_size - 1)

            # Count points in each box
            if grid_points.shape[1] == 2:
                boxes, counts = np.unique(
                    grid_points[:, 0] * grid_size + grid_points[:, 1],
                    return_counts=True
                )
            elif grid_points.shape[1] == 3:
                boxes, counts = np.unique(
                    grid_points[:, 0] * grid_size * grid_size +
                    grid_points[:, 1] * grid_size +
                    grid_points[:, 2],
                    return_counts=True
                )
            else:
                # General case
                unique_boxes = {}
                for point in grid_points:
                    key = tuple(point)
                    unique_boxes[key] = unique_boxes.get(key, 0) + 1
                counts = np.array(list(unique_boxes.values()))

            # Calculate Shannon entropy
            probabilities = counts / len(points)
            entropy = -np.sum(probabilities * np.log(probabilities + 1e-10))
            information.append(entropy)

        information = np.array(information)

        # Calculate dimension from scaling
        log_scales = -np.log(scales)
        valid = np.isfinite(log_scales) & np.isfinite(information)

        if np.sum(valid) < 3:
            raise ValueError("Insufficient valid data points")

        slope, intercept, r_value, p_value, std_err = linregress(
            log_scales[valid], information[valid]
        )
        dimension = slope

        confidence = 1.96 * std_err
        confidence_interval = (dimension - confidence, dimension + confidence)

        return FractalDimensionResult(
            method="information",
            dimension=dimension,
            error=std_err,
            r_squared=r_value ** 2,
            scales=scales[valid],
            measures=information[valid],
            confidence_interval=confidence_interval,
            metadata={
                "num_points": len(points),
                "p_value": p_value
            }
        )


class SelfSimilarityAnalyzer:
    """Analyze self-similarity properties of fractals."""

    @staticmethod
    def find_scaling_ratio(points: np.ndarray,
                          test_scales: List[float] = None) -> Dict[str, Any]:
        """Find the scaling ratio for self-similar structures."""
        if test_scales is None:
            test_scales = [2.0, 3.0, 4.0, 5.0, 7.0, 10.0]

        results = {}
        points = np.array(points)

        # Normalize points
        center = np.mean(points, axis=0)
        centered = points - center

        for scale in test_scales:
            # Scale down the points
            scaled = centered / scale

            # Find best match by translation
            min_error = np.inf
            best_translation = None

            # Try different translations
            for _ in range(100):
                # Random translation
                translation = centered[np.random.randint(len(centered))]

                # Compute matching error
                translated = scaled + translation

                # Find nearest neighbors
                from scipy.spatial import KDTree
                tree = KDTree(centered)
                distances, _ = tree.query(translated)
                error = np.mean(distances)

                if error < min_error:
                    min_error = error
                    best_translation = translation

            results[scale] = {
                "error": min_error,
                "translation": best_translation
            }

        # Find best scale
        best_scale = min(results.keys(), key=lambda k: results[k]["error"])

        return {
            "best_scale": best_scale,
            "best_error": results[best_scale]["error"],
            "all_results": results
        }

    @staticmethod
    def lacunarity(image: np.ndarray,
                  box_sizes: Optional[List[int]] = None) -> Dict[str, Any]:
        """Calculate lacunarity (measure of gappiness) of a binary image."""
        if box_sizes is None:
            max_size = min(image.shape) // 4
            box_sizes = [2**i for i in range(1, int(np.log2(max_size)) + 1)]

        lacunarities = []

        for box_size in box_sizes:
            # Sliding box algorithm
            masses = []

            for i in range(0, image.shape[0] - box_size + 1):
                for j in range(0, image.shape[1] - box_size + 1):
                    box = image[i:i+box_size, j:j+box_size]
                    mass = np.sum(box)
                    masses.append(mass)

            masses = np.array(masses)

            if len(masses) > 0 and np.mean(masses) > 0:
                # Lacunarity = variance/mean^2 + 1
                lac = np.var(masses) / (np.mean(masses) ** 2) + 1
                lacunarities.append(lac)
            else:
                lacunarities.append(np.nan)

        return {
            "box_sizes": box_sizes,
            "lacunarities": lacunarities,
            "mean_lacunarity": np.nanmean(lacunarities)
        }


def analyze_fractal_dimensions(output_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Production analysis of fractal dimensions for various sets."""
    if output_dir is None:
        output_dir = Config.RESULTS_DIR
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    calculator = FractalDimensionCalculator()
    # Sample Cantor set
    generator = FractalGenerator()
    cantor = generator.cantor_set(iterations=10)
    
    # Extract points for box-counting
    points = []
    for start, end in cantor:
        points.append([start, 0])
        points.append([end, 0])
    
    res = calculator.box_counting_dimension(np.array(points))
    results = {
        "cantor_dim": res.dimension,
        "r_squared": res.r_squared
    }
    
    if output_dir:
        import json
        with open(output_dir / "fractal_analysis.json", 'w') as f:
            json.dump(results, f, indent=2)
            
    return results

def run_dimension_analysis(output_dir: Optional[Path] = None) -> None:
    """Analyze dimensions of well-known fractals."""
    if output_dir is None:
        output_dir = Config.RESULTS_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("FRACTAL DIMENSION ANALYSIS")
    print("=" * 80)

    results = {}
    calculator = FractalDimensionCalculator()
    generator = FractalGenerator()

    # 1. Cantor Set (theoretical dimension: log(2)/log(3) ≈ 0.631)
    print("\n--- Cantor Set ---")
    cantor = generator.cantor_set(iterations=8)
    cantor_points = []
    for start, end in cantor:
        # Sample points from each interval
        cantor_points.extend(np.linspace(start, end, 10)[:, np.newaxis])
    cantor_points = np.array(cantor_points)

    cantor_dim = calculator.box_counting_dimension(cantor_points, num_scales=15)
    theoretical_cantor = np.log(2) / np.log(3)
    print(f"Calculated dimension: {cantor_dim.dimension:.4f}")
    print(f"Theoretical dimension: {theoretical_cantor:.4f}")
    print(f"Error: {abs(cantor_dim.dimension - theoretical_cantor):.4f}")
    results["cantor_set"] = cantor_dim.to_dict()

    # 2. Sierpinski Triangle (theoretical dimension: log(3)/log(2) ≈ 1.585)
    print("\n--- Sierpinski Triangle ---")
    sierpinski = generator.sierpinski_triangle(iterations=7)
    sierpinski_points = np.column_stack(np.where(sierpinski > 0))

    sierp_dim = calculator.box_counting_dimension(sierpinski_points)
    theoretical_sierp = np.log(3) / np.log(2)
    print(f"Calculated dimension: {sierp_dim.dimension:.4f}")
    print(f"Theoretical dimension: {theoretical_sierp:.4f}")
    print(f"Error: {abs(sierp_dim.dimension - theoretical_sierp):.4f}")
    results["sierpinski_triangle"] = sierp_dim.to_dict()

    # 3. Koch Snowflake boundary (theoretical dimension: log(4)/log(3) ≈ 1.262)
    print("\n--- Koch Snowflake ---")
    koch = generator.koch_snowflake(iterations=6)

    koch_dim = calculator.box_counting_dimension(koch)
    theoretical_koch = np.log(4) / np.log(3)
    print(f"Calculated dimension: {koch_dim.dimension:.4f}")
    print(f"Theoretical dimension: {theoretical_koch:.4f}")
    print(f"Error: {abs(koch_dim.dimension - theoretical_koch):.4f}")
    results["koch_snowflake"] = koch_dim.to_dict()

    # 4. Lorenz Attractor (typical dimension: ~2.06)
    print("\n--- Lorenz Attractor ---")
    lorenz = generator.lorenz_attractor(num_points=20000)

    # Use correlation dimension for strange attractors
    lorenz_dim = calculator.correlation_dimension(lorenz, sample_size=5000)
    print(f"Calculated correlation dimension: {lorenz_dim.dimension:.4f}")
    print("Typical dimension: ~2.06")
    results["lorenz_attractor"] = lorenz_dim.to_dict()

    # 5. Henon Map (typical dimension: ~1.26)
    print("\n--- Henon Map ---")
    henon = generator.henon_map(num_points=20000)

    henon_dim = calculator.correlation_dimension(henon, sample_size=5000)
    print(f"Calculated correlation dimension: {henon_dim.dimension:.4f}")
    print("Typical dimension: ~1.26")
    results["henon_map"] = henon_dim.to_dict()

    # 6. Mandelbrot Set boundary (theoretical dimension: 2.0)
    print("\n--- Mandelbrot Set Boundary ---")
    print("Generating boundary points (this may take a moment)...")
    mandel_boundary = generator.mandelbrot_boundary(resolution=500)

    if len(mandel_boundary) > 100:
        mandel_dim = calculator.box_counting_dimension(mandel_boundary)
        print(f"Calculated dimension: {mandel_dim.dimension:.4f}")
        print("Theoretical dimension: 2.0 (conjectured)")
        results["mandelbrot_boundary"] = mandel_dim.to_dict()
    else:
        print("Insufficient boundary points found")

    # Save results
    with open(output_dir / "fractal_dimensions.json", 'w') as f:
        json.dump(results, f, indent=2)

    # Create summary table
    print("\n" + "=" * 80)
    print("SUMMARY OF FRACTAL DIMENSIONS")
    print("=" * 80)
    print(f"{'Fractal':<25} {'Calculated':<12} {'Theoretical':<12} {'Error':<10}")
    print("-" * 80)

    dimension_map = {
        "cantor_set": ("Cantor Set", np.log(2)/np.log(3)),
        "sierpinski_triangle": ("Sierpinski Triangle", np.log(3)/np.log(2)),
        "koch_snowflake": ("Koch Snowflake", np.log(4)/np.log(3)),
        "lorenz_attractor": ("Lorenz Attractor", 2.06),
        "henon_map": ("Henon Map", 1.26),
        "mandelbrot_boundary": ("Mandelbrot Boundary", 2.0)
    }

    for key, (name, theoretical) in dimension_map.items():
        if key in results:
            calc_dim = results[key]["dimension"]
            error = abs(calc_dim - theoretical)
            print(f"{name:<25} {calc_dim:<12.4f} {theoretical:<12.4f} {error:<10.4f}")

    return results


def demonstrate_methods():
    """Demonstrate different dimension calculation methods."""
    print("\n" + "=" * 80)
    print("COMPARISON OF DIMENSION CALCULATION METHODS")
    print("=" * 80)

    generator = FractalGenerator()
    calculator = FractalDimensionCalculator()

    # Generate a test fractal (Sierpinski triangle)
    print("\nGenerating Sierpinski triangle...")
    sierpinski = generator.sierpinski_triangle(iterations=7)
    points = np.column_stack(np.where(sierpinski > 0))

    # Subsample for faster computation
    if len(points) > 5000:
        indices = np.random.choice(len(points), 5000, replace=False)
        points = points[indices]

    theoretical = np.log(3) / np.log(2)
    print(f"Theoretical dimension: {theoretical:.4f}")
    print(f"Number of points: {len(points)}")

    # Test different methods
    methods_results = {}

    print("\n1. Box-counting dimension:")
    box_dim = calculator.box_counting_dimension(points)
    print(f"   Dimension: {box_dim.dimension:.4f} +/- {box_dim.error:.4f}")
    print(f"   R-squared: {box_dim.r_squared:.4f}")
    methods_results["box_counting"] = box_dim

    print("\n2. Hausdorff dimension (covering):")
    try:
        haus_dim = calculator.hausdorff_dimension(points, num_scales=10)
        print(f"   Dimension: {haus_dim.dimension:.4f} +/- {haus_dim.error:.4f}")
        print(f"   R-squared: {haus_dim.r_squared:.4f}")
        methods_results["hausdorff"] = haus_dim
    except Exception as e:
        print(f"   Error: {e}")

    print("\n3. Correlation dimension:")
    corr_dim = calculator.correlation_dimension(points, sample_size=1000)
    print(f"   Dimension: {corr_dim.dimension:.4f} +/- {corr_dim.error:.4f}")
    print(f"   R-squared: {corr_dim.r_squared:.4f}")
    methods_results["correlation"] = corr_dim

    print("\n4. Information dimension:")
    info_dim = calculator.information_dimension(points)
    print(f"   Dimension: {info_dim.dimension:.4f} +/- {info_dim.error:.4f}")
    print(f"   R-squared: {info_dim.r_squared:.4f}")
    methods_results["information"] = info_dim

    # Compare methods
    print("\n" + "-" * 60)
    print("Method Comparison:")
    print(f"{'Method':<20} {'Dimension':<15} {'Error from Theory':<15}")
    print("-" * 60)

    for method_name, result in methods_results.items():
        error = abs(result.dimension - theoretical)
        print(f"{method_name:<20} {result.dimension:<15.4f} {error:<15.4f}")

    return methods_results


if __name__ == "__main__":
    # Run demonstrations
    print("Starting fractal analysis demonstrations...")

    # Demonstrate different calculation methods
    methods_results = demonstrate_methods()

    # Analyze known fractals
    fractal_results = analyze_fractal_dimensions()

    print("\n" + "=" * 80)
    print("Fractal analysis complete!")
    print("Results saved to experiments/results/")
    print("=" * 80)