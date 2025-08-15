import numpy as np

def ndvi(nir, red, eps=1e-6):
    return (nir - red) / (nir + red + eps)

def ndwi(green, nir, eps=1e-6):
    return (green - nir) / (green + nir + eps)

def mndwi(green, swir1, eps=1e-6):
    return (green - swir1) / (green + swir1 + eps)

def bsi(blue, red, nir, swir1, eps=1e-6):
    # Bare Soil Index (Rikimaru 2002 variant)
    num = (red + swir1) - (nir + blue)
    den = (red + swir1) + (nir + blue) + eps
    return num / den
