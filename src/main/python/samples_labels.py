# Sample labels for sand particle analysis
# Represents the reference values for different sand size grades

# Format: 6 columns represent the size grades:
# 0.075~0.15mm, 0.15~0.3mm, 0.3~0.6mm, 0.6~1.18mm, 1.18~2.36mm, 2.36~4.75mm

# Export as LABELS for compatibility
LABELS = [
    # Sample reference values for different sand types with updated distributions
    [0.03, 0.08, 0.20, 0.30, 0.25, 0.14],  # Standard sand mix
    [0.02, 0.10, 0.25, 0.28, 0.23, 0.12],  # Fine grain dominant
    [0.01, 0.05, 0.15, 0.35, 0.30, 0.14],  # Medium grain dominant
    [0.02, 0.07, 0.18, 0.33, 0.25, 0.15],  # Balanced distribution
    [0.04, 0.12, 0.22, 0.25, 0.23, 0.14],  # Mixed grain type
    [0.02, 0.08, 0.20, 0.32, 0.25, 0.13]   # Optimized mix
]



# Also export as expected in the application
__all__ = ['LABELS']
