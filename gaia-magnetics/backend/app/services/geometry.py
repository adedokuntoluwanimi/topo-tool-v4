"""
Geometry computation service.
Handles coordinate conversion, distance calculation, and train/predict splitting.
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional
from math import radians, sin, cos, sqrt, atan2


def detect_utm_zone(lon: float, lat: float) -> int:
    """
    Detect UTM zone number from longitude.
    
    Args:
        lon: Longitude in degrees
        lat: Latitude in degrees (used for hemisphere)
    
    Returns:
        EPSG code for the UTM zone
    """
    zone_number = int((lon + 180) / 6) + 1
    
    # Handle special cases for Norway and Svalbard
    if 56 <= lat < 64 and 3 <= lon < 12:
        zone_number = 32
    elif 72 <= lat < 84:
        if 0 <= lon < 9:
            zone_number = 31
        elif 9 <= lon < 21:
            zone_number = 33
        elif 21 <= lon < 33:
            zone_number = 35
        elif 33 <= lon < 42:
            zone_number = 37
    
    # Determine hemisphere
    if lat >= 0:
        epsg = 32600 + zone_number  # Northern hemisphere
    else:
        epsg = 32700 + zone_number  # Southern hemisphere
    
    return epsg


def haversine_distance(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    """
    Calculate distance between two geographic points using Haversine formula.
    
    Args:
        lon1, lat1: First point (degrees)
        lon2, lat2: Second point (degrees)
    
    Returns:
        Distance in meters
    """
    R = 6371000  # Earth's radius in meters
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lon = radians(lon2 - lon1)
    
    a = sin(delta_lat/2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c


def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """
    Calculate Euclidean distance between two points.
    
    Args:
        x1, y1: First point
        x2, y2: Second point
    
    Returns:
        Distance in same units as input
    """
    return sqrt((x2 - x1)**2 + (y2 - y1)**2)


def compute_cumulative_distance(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    coordinate_system: str = "projected"
) -> pd.DataFrame:
    """
    Calculate cumulative distance along traverse.
    
    Args:
        df: DataFrame with coordinates
        x_col: Column name for X coordinate
        y_col: Column name for Y coordinate
        coordinate_system: "projected" (meters) or "geographic" (lat/lon)
    
    Returns:
        DataFrame with added 'distance' column
    """
    df = df.copy()
    
    distances = [0.0]
    
    for i in range(1, len(df)):
        x1, y1 = df.iloc[i-1][x_col], df.iloc[i-1][y_col]
        x2, y2 = df.iloc[i][x_col], df.iloc[i][y_col]
        
        if coordinate_system == "geographic":
            d = haversine_distance(x1, y1, x2, y2)
        else:
            d = euclidean_distance(x1, y1, x2, y2)
        
        distances.append(distances[-1] + d)
    
    df["distance"] = distances
    
    return df


def generate_prediction_stations(
    min_distance: float,
    max_distance: float,
    spacing: float
) -> np.ndarray:
    """
    Generate evenly spaced prediction station distances.
    
    Args:
        min_distance: Start of traverse
        max_distance: End of traverse
        spacing: Distance between stations
    
    Returns:
        Array of distances for prediction stations
    """
    return np.arange(min_distance, max_distance + spacing, spacing)


def interpolate_coordinates(
    train_df: pd.DataFrame,
    predict_distances: np.ndarray,
    x_col: str,
    y_col: str
) -> pd.DataFrame:
    """
    Interpolate X, Y coordinates for prediction stations.
    
    Args:
        train_df: DataFrame with measured stations (must have 'distance' column)
        predict_distances: Distances for prediction stations
        x_col: Column name for X coordinate
        y_col: Column name for Y coordinate
    
    Returns:
        DataFrame with distance, x, y columns for prediction stations
    """
    # Sort by distance for interpolation
    train_sorted = train_df.sort_values("distance")
    
    # Interpolate X and Y
    x_interp = np.interp(
        predict_distances,
        train_sorted["distance"].values,
        train_sorted[x_col].values
    )
    
    y_interp = np.interp(
        predict_distances,
        train_sorted["distance"].values,
        train_sorted[y_col].values
    )
    
    return pd.DataFrame({
        "distance": predict_distances,
        "x": x_interp,
        "y": y_interp
    })


def compute_geometry(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    value_col: str,
    coordinate_system: str = "projected"
) -> pd.DataFrame:
    """
    Compute geometry for input data.
    
    Args:
        df: Raw input DataFrame
        x_col: X coordinate column
        y_col: Y coordinate column
        value_col: Measured value column
        coordinate_system: "projected" or "geographic"
    
    Returns:
        DataFrame with standardized columns (distance, x, y, value)
    """
    # Compute cumulative distance
    df = compute_cumulative_distance(df, x_col, y_col, coordinate_system)
    
    # Standardize column names
    result = pd.DataFrame({
        "distance": df["distance"],
        "x": df[x_col],
        "y": df[y_col],
        "value": df[value_col]
    })
    
    return result


def split_train_predict(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    value_col: str,
    station_spacing: float,
    coordinate_system: str = "projected"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into training and prediction sets for SPARSE scenario.
    
    For sparse scenario:
    - Training: original measured points
    - Prediction: generated stations at regular spacing
    
    Args:
        df: Input DataFrame with raw data
        x_col: X coordinate column
        y_col: Y coordinate column
        value_col: Value column
        station_spacing: Distance between prediction stations
        coordinate_system: "projected" or "geographic"
    
    Returns:
        Tuple of (train_df, predict_df)
    """
    # Compute geometry for training data
    train_df = compute_geometry(df, x_col, y_col, value_col, coordinate_system)
    
    # Generate prediction stations
    min_dist = train_df["distance"].min()
    max_dist = train_df["distance"].max()
    predict_distances = generate_prediction_stations(min_dist, max_dist, station_spacing)
    
    # Remove prediction distances that are too close to measured points
    # (within 10% of station spacing)
    threshold = station_spacing * 0.1
    measured_distances = train_df["distance"].values
    
    filtered_distances = []
    for d in predict_distances:
        min_diff = np.min(np.abs(measured_distances - d))
        if min_diff > threshold:
            filtered_distances.append(d)
    
    predict_distances = np.array(filtered_distances)
    
    # Interpolate coordinates for prediction stations
    predict_df = interpolate_coordinates(train_df, predict_distances, "x", "y")
    
    # Prepare final DataFrames
    # Train: distance, x, y, value
    train_df = train_df[["distance", "x", "y", "value"]]
    
    # Predict: distance, x, y (no value - that's what we're predicting)
    predict_df = predict_df[["distance", "x", "y"]]
    
    return train_df, predict_df


def split_train_predict_explicit(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    value_col: str,
    coordinate_system: str = "projected"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Split data into training and prediction sets for EXPLICIT scenario.
    
    For explicit scenario:
    - Training: rows WITH values (not null/empty)
    - Prediction: rows WITHOUT values (null/empty)
    
    Args:
        df: Input DataFrame with raw data
        x_col: X coordinate column
        y_col: Y coordinate column
        value_col: Value column
        coordinate_system: "projected" or "geographic"
    
    Returns:
        Tuple of (train_df, predict_df)
    """
    # Compute cumulative distance for ALL rows first
    df = compute_cumulative_distance(df, x_col, y_col, coordinate_system)
    
    # Split based on whether value is present
    # Check for NaN, empty string, or whitespace
    has_value = df[value_col].notna() & (df[value_col].astype(str).str.strip() != '')
    
    train_rows = df[has_value].copy()
    predict_rows = df[~has_value].copy()
    
    # Standardize train DataFrame
    train_df = pd.DataFrame({
        "distance": train_rows["distance"],
        "x": train_rows[x_col],
        "y": train_rows[y_col],
        "value": pd.to_numeric(train_rows[value_col], errors='coerce')
    })
    
    # Standardize predict DataFrame (no value column)
    predict_df = pd.DataFrame({
        "distance": predict_rows["distance"],
        "x": predict_rows[x_col],
        "y": predict_rows[y_col]
    })
    
    return train_df, predict_df
