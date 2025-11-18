#!/usr/bin/env python3
"""
Sensitivity analysis for R-OSSE horn profile scoring components.
Determines min/max ranges for each penalty to enable proper normalization.
"""

import numpy as np
from itertools import product
import json

def calculate_curvature(x, y):
    """Calculate curvature along the profile."""
    kappa = np.zeros(len(x))
    for i in range(1, len(x) - 1):
        dx = (x[i + 1] - x[i - 1]) / 2
        dy = (y[i + 1] - y[i - 1]) / 2
        ddx = x[i + 1] - 2 * x[i] + x[i - 1]
        ddy = y[i + 1] - 2 * y[i] + y[i - 1]
        
        num = abs(dx * ddy - dy * ddx)
        denom = (dx * dx + dy * dy) ** 1.5
        
        kappa[i] = num / denom if denom > 1e-10 else 0
    
    return kappa

def rosse_profile(k, r, m, b, q, r0, R, a0_deg, a_deg, N=200):
    """Generate R-OSSE horn profile."""
    a0 = a0_deg * np.pi / 180
    a = a_deg * np.pi / 180
    
    # Validation
    if k <= 0 or r <= 0 or m <= 0 or m >= 1 or b <= 0 or q <= 0:
        return None
    if r0 <= 0 or R <= 0 or r0 >= R:
        return None
    
    t = np.linspace(0, 1, N)
    
    c1 = (k * r0) ** 2
    c2 = 2 * k * r0 * np.tan(a0)
    c3 = np.tan(a) ** 2
    
    inside = c2 * c2 - 4 * c3 * (c1 - (R + r0 * (k - 1)) ** 2)
    
    if inside <= 0 or not np.isfinite(inside):
        return None
    
    L = (np.sqrt(inside) - c2) / (2 * c3)
    
    if not np.isfinite(L) or L <= 0:
        return None
    
    sqrt_term1 = np.sqrt(r * r + m * m)
    sqrt_term2 = np.sqrt(r * r + (t - m) ** 2)
    
    x = L * (sqrt_term1 - sqrt_term2) + b * L * (np.sqrt(r * r + (1 - m) ** 2) - sqrt_term1) * t * t
    
    sqrt_term3 = np.sqrt(1 + c3 * (t - 1) ** 2)
    y1 = np.sqrt(c1 + c2 * (L * t) + c3 * (L * t) ** 2) + r0 * (1 - k)
    y2 = R + L * (1 - sqrt_term3)
    w = t ** q
    y = (1 - w) * y1 + w * y2
    
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        return None
    
    return x, y

def compute_penalties(x, y):
    """Compute all five penalty components."""
    kappa = calculate_curvature(x, y)
    
    N = len(x)
    lo = int(0.05 * N)
    hi = int(0.90 * N)
    
    x_mid = x[lo:hi]
    y_mid = y[lo:hi]
    k_mid = kappa[lo:hi]
    
    # 1. Curvature derivative smoothness
    dk = np.gradient(k_mid)
    curv_var = np.mean(dk ** 2)
    
    # 2. Kink penalty
    kink_penalty = np.max(k_mid) ** 2
    
    # 3. Slope smoothness
    dy = np.gradient(y_mid)
    ddy = np.gradient(dy)
    slope_penalty = np.mean(ddy ** 2)
    
    # 4. Monotonicity penalty
    dkappa = np.diff(k_mid)
    monotonic_penalty = np.sum(np.maximum(0, -dkappa))
    
    # 5. Z-height penalty
    z_height = x[-1] - x[0]
    z_height_penalty = (z_height / 100.0) ** 2
    
    return {
        'curv_var': curv_var,
        'kink': kink_penalty,
        'slope': slope_penalty,
        'monotonic': monotonic_penalty,
        'z_height': z_height_penalty
    }

def run_sensitivity_analysis():
    """Sample parameter space and find min/max for each penalty."""
    
    # Parameter bounds
    param_ranges = {
        'k': np.linspace(0.1, 10.0, 5),
        'r': np.linspace(0.05, 1.0, 5),
        'm': np.linspace(0.1, 0.9, 5),
        'b': np.linspace(0.1, 3.0, 5),
        'q': np.linspace(1.0, 5.0, 5),
        'r0': np.linspace(5, 100, 4),
        'R': np.linspace(50, 500, 4),
        'a0': np.linspace(-30, 30, 4),
        'a': np.linspace(10, 80, 4)
    }
    
    # Fixed acoustic parameters for initial sweep
    fixed_acoustics = {
        'r0': 20.5,
        'R': 117,
        'a0': 5,
        'a': 50
    }
    
    penalties_data = {
        'curv_var': [],
        'kink': [],
        'slope': [],
        'monotonic': [],
        'z_height': []
    }
    
    print("Running sensitivity analysis...")
    count = 0
    total = len(param_ranges['k']) * len(param_ranges['r']) * len(param_ranges['m']) * \
            len(param_ranges['b']) * len(param_ranges['q'])
    
    # Sweep shape parameters
    for k in param_ranges['k']:
        for r in param_ranges['r']:
            for m in param_ranges['m']:
                for b in param_ranges['b']:
                    for q in param_ranges['q']:
                        count += 1
                        if count % 50 == 0:
                            print(f"  Sampled {count}/{total} configurations")
                        
                        result = rosse_profile(k, r, m, b, q, 
                                             fixed_acoustics['r0'], fixed_acoustics['R'],
                                             fixed_acoustics['a0'], fixed_acoustics['a'])
                        
                        if result is not None:
                            x, y = result
                            penalties = compute_penalties(x, y)
                            for key, val in penalties.items():
                                penalties_data[key].append(val)
    
    # Also sweep acoustic parameters with fixed shape parameters
    print("  Sweeping acoustic parameters...")
    shape_fixed = {'k': 1.5, 'r': 0.5, 'm': 0.5, 'b': 1.0, 'q': 2.0}
    
    for r0 in param_ranges['r0']:
        for R in param_ranges['R']:
            for a0 in param_ranges['a0']:
                for a in param_ranges['a']:
                    result = rosse_profile(shape_fixed['k'], shape_fixed['r'], shape_fixed['m'],
                                         shape_fixed['b'], shape_fixed['q'],
                                         r0, R, a0, a)
                    
                    if result is not None:
                        x, y = result
                        penalties = compute_penalties(x, y)
                        for key, val in penalties.items():
                            penalties_data[key].append(val)
    
    # Compute statistics
    stats = {}
    for penalty_name, values in penalties_data.items():
        if values:
            valid_values = [v for v in values if np.isfinite(v) and v > 0]
            if valid_values:
                stats[penalty_name] = {
                    'min': float(np.min(valid_values)),
                    'max': float(np.max(valid_values)),
                    'mean': float(np.mean(valid_values)),
                    'median': float(np.median(valid_values)),
                    'std': float(np.std(valid_values)),
                    'count': len(valid_values)
                }
            else:
                stats[penalty_name] = {
                    'min': None,
                    'max': None,
                    'mean': None,
                    'median': None,
                    'std': None,
                    'count': 0
                }
        else:
            stats[penalty_name] = {
                'min': None,
                'max': None,
                'mean': None,
                'median': None,
                'std': None,
                'count': 0
            }
    
    return stats

if __name__ == '__main__':
    stats = run_sensitivity_analysis()
    
    print("\n" + "="*70)
    print("SENSITIVITY ANALYSIS RESULTS")
    print("="*70)
    
    normalization = {}
    for penalty_name, data in stats.items():
        print(f"\n{penalty_name.upper()}:")
        print(f"  Min:    {data['min']:.6e}")
        print(f"  Max:    {data['max']:.6e}")
        print(f"  Mean:   {data['mean']:.6e}")
        print(f"  Median: {data['median']:.6e}")
        print(f"  Std:    {data['std']:.6e}")
        print(f"  Count:  {data['count']}")
        
        if data['min'] is not None and data['max'] is not None:
            # Use log scale for better handling of wide ranges
            log_min = np.log10(data['min'])
            log_max = np.log10(data['max'])
            normalization[penalty_name] = {
                'min': data['min'],
                'max': data['max'],
                'log_min': float(log_min),
                'log_max': float(log_max),
                'log_range': float(log_max - log_min)
            }
    
    print("\n" + "="*70)
    print("NORMALIZATION CONSTANTS (for JavaScript)")
    print("="*70)
    print("\nConst object to add to JavaScript:\n")
    print("const PENALTY_NORMALIZATION = {")
    for penalty_name, norm in normalization.items():
        print(f"  {penalty_name}: {{")
        print(f"    min: {norm['min']:.6e},")
        print(f"    max: {norm['max']:.6e},")
        print(f"    logMin: {norm['log_min']:.6f},")
        print(f"    logMax: {norm['log_max']:.6f},")
        print(f"    logRange: {norm['log_range']:.6f}")
        print(f"  }},")
    print("};")
    
    # Save to JSON file
    with open('penalty_normalization.json', 'w') as f:
        json.dump(normalization, f, indent=2)
    
    print("\n✓ Results saved to penalty_normalization.json")
