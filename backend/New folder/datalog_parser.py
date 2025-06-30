
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class DatalogParseError(Exception):
    """Custom exception for datalog parsing errors"""
    pass

def parse_datalog(datalog_path: str, platform: Optional[str] = None) -> pd.DataFrame:
    """
    Parse datalog file based on platform (Subaru/Hondata/Auto-detect)

    Args:
        datalog_path: Path to the datalog file
        platform: Platform type ('Subaru', 'Hondata', or None for auto-detect)

    Returns:
        pandas.DataFrame: Parsed datalog data

    Raises:
        DatalogParseError: If parsing fails
    """
    try:
        # Validate file exists
        if not Path(datalog_path).exists():
            raise DatalogParseError(f"Datalog file not found: {datalog_path}")

        # Auto-detect platform if not specified
        if platform is None:
            platform = detect_platform_from_datalog(datalog_path)
            logger.info(f"Auto-detected platform: {platform}")

        # Parse based on platform
        if platform.lower() == "subaru":
            return parse_subaru_datalog(datalog_path)
        elif platform.lower() == "hondata":
            return parse_hondata_datalog(datalog_path)
        else:
            # Try generic CSV parsing as fallback
            logger.warning(f"Unknown platform '{platform}', attempting generic CSV parsing")
            return parse_generic_datalog(datalog_path)

    except Exception as e:
        logger.error(f"Failed to parse datalog {datalog_path}: {str(e)}")
        raise DatalogParseError(f"Failed to parse datalog: {str(e)}")

def detect_platform_from_datalog(datalog_path: str) -> str:
    """
    Auto-detect platform based on datalog content

    Args:
        datalog_path: Path to the datalog file

    Returns:
        str: Detected platform ('Subaru', 'Hondata', or 'Unknown')
    """
    try:
        # Read first few lines to detect format
        with open(datalog_path, 'r', encoding='utf-8', errors='ignore') as f:
            first_lines = [f.readline().lower() for _ in range(10)]

        content = ' '.join(first_lines)

        # Subaru/RomRaider indicators
        subaru_indicators = [
            'a/f correction', 'engine speed', 'coolant temperature',
            'mass airflow', 'manifold absolute pressure', 'ignition total timing',
            'romraider', 'volumetric efficiency'
        ]

        # Hondata indicators
        hondata_indicators = [
            'hondata', 'kpro', 's300', 'flashpro',
            'vtec', 'cam angle', 'gear position'
        ]

        subaru_score = sum(1 for indicator in subaru_indicators if indicator in content)
        hondata_score = sum(1 for indicator in hondata_indicators if indicator in content)

        if subaru_score > hondata_score and subaru_score > 0:
            return "Subaru"
        elif hondata_score > 0:
            return "Hondata"
        else:
            return "Unknown"

    except Exception as e:
        logger.warning(f"Platform detection failed: {e}")
        return "Unknown"

def parse_subaru_datalog(datalog_path: str) -> pd.DataFrame:
    """
    Parse Subaru/RomRaider datalog format

    Args:
        datalog_path: Path to the datalog file

    Returns:
        pandas.DataFrame: Parsed datalog data
    """
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(datalog_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            raise DatalogParseError("Could not read file with any supported encoding")

        # Clean column names
        df.columns = df.columns.str.strip()

        # Validate required Subaru columns
        required_columns = ['Time (msec)', 'Engine Speed (rpm)']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            # Try alternative column names
            alt_mappings = {
                'Time (msec)': ['Time', 'Timestamp', 'Time(msec)', 'Time (ms)'],
                'Engine Speed (rpm)': ['RPM', 'Engine RPM', 'EngineSpeed', 'Engine Speed']
            }

            for req_col in missing_columns:
                found = False
                for alt_col in alt_mappings.get(req_col, []):
                    if alt_col in df.columns:
                        df.rename(columns={alt_col: req_col}, inplace=True)
                        found = True
                        break

                if not found:
                    logger.warning(f"Missing expected column: {req_col}")

        # Convert numeric columns
        numeric_columns = df.select_dtypes(include=[object]).columns
        for col in numeric_columns:
            if col != 'Time (msec)':  # Skip time column for now
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Handle time column
        if 'Time (msec)' in df.columns:
            df['Time (msec)'] = pd.to_numeric(df['Time (msec)'], errors='coerce')

        # Remove rows with all NaN values
        df = df.dropna(how='all')

        # Add metadata
        df.attrs['platform'] = 'Subaru'
        df.attrs['parsed_at'] = datetime.now().isoformat()
        df.attrs['total_rows'] = len(df)

        logger.info(f"Successfully parsed Subaru datalog: {len(df)} rows, {len(df.columns)} columns")
        return df

    except Exception as e:
        raise DatalogParseError(f"Failed to parse Subaru datalog: {str(e)}")

def parse_hondata_datalog(datalog_path: str) -> pd.DataFrame:
    """
    Parse Hondata datalog format

    Args:
        datalog_path: Path to the datalog file

    Returns:
        pandas.DataFrame: Parsed datalog data
    """
    try:
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252']
        df = None

        for encoding in encodings:
            try:
                df = pd.read_csv(datalog_path, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue

        if df is None:
            raise DatalogParseError("Could not read file with any supported encoding")

        # Clean column names
        df.columns = df.columns.str.strip()

        # Validate typical Hondata columns
        expected_columns = ['Time', 'RPM', 'MAP', 'TPS']
        missing_columns = [col for col in expected_columns if col not in df.columns]

        if len(missing_columns) == len(expected_columns):
            logger.warning("No typical Hondata columns found, treating as generic CSV")

        # Convert numeric columns
        numeric_columns = df.select_dtypes(include=[object]).columns
        for col in numeric_columns:
            if 'time' not in col.lower():  # Skip time columns for now
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # Handle time column
        time_columns = [col for col in df.columns if 'time' in col.lower()]
        for time_col in time_columns:
            df[time_col] = pd.to_numeric(df[time_col], errors='coerce')

        # Remove rows with all NaN values
        df = df.dropna(how='all')

        # Add metadata
        df.attrs['platform'] = 'Hondata'
        df.attrs['parsed_at'] = datetime.now().isoformat()
        df.attrs['total_rows'] = len(df)

        logger.info(f"Successfully parsed Hondata datalog: {len(df)} rows, {len(df.columns)} columns")
        return df

    except Exception as e:
        raise DatalogParseError(f"Failed to parse Hondata datalog: {str(e)}")

def parse_generic_datalog(datalog_path: str) -> pd.DataFrame:
    """
    Generic CSV datalog parser as fallback

    Args:
        datalog_path: Path to the datalog file

    Returns:
        pandas.DataFrame: Parsed datalog data
    """
    try:
        # Try different separators and encodings
        separators = [',', ';', '\t']
        encodings = ['utf-8', 'latin-1', 'cp1252']

        df = None
        for encoding in encodings:
            for sep in separators:
                try:
                    test_df = pd.read_csv(datalog_path, sep=sep, encoding=encoding, nrows=5)
                    if len(test_df.columns) > 1:  # Valid CSV should have multiple columns
                        df = pd.read_csv(datalog_path, sep=sep, encoding=encoding)
                        break
                except:
                    continue
            if df is not None:
                break

        if df is None:
            raise DatalogParseError("Could not parse as CSV with any common separator or encoding")

        # Clean column names
        df.columns = df.columns.str.strip()

        # Convert numeric columns
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                if not numeric_series.isna().all():  # If at least some values are numeric
                    df[col] = numeric_series

        # Remove rows with all NaN values
        df = df.dropna(how='all')

        # Add metadata
        df.attrs['platform'] = 'Generic'
        df.attrs['parsed_at'] = datetime.now().isoformat()
        df.attrs['total_rows'] = len(df)

        logger.info(f"Successfully parsed generic datalog: {len(df)} rows, {len(df.columns)} columns")
        return df

    except Exception as e:
        raise DatalogParseError(f"Failed to parse generic datalog: {str(e)}")

def detect_issues(datalog_df: pd.DataFrame, platform: str) -> List[Dict[str, Any]]:
    """
    Detect issues in the parsed datalog

    Args:
        datalog_df: Parsed datalog DataFrame
        platform: Platform type

    Returns:
        List of detected issues
    """
    issues = []

    try:
        if platform.lower() == "subaru":
            issues.extend(detect_subaru_issues(datalog_df))
        elif platform.lower() == "hondata":
            issues.extend(detect_hondata_issues(datalog_df))
        else:
            issues.extend(detect_generic_issues(datalog_df))

        logger.info(f"Detected {len(issues)} issues in datalog")
        return issues

    except Exception as e:
        logger.error(f"Issue detection failed: {e}")
        return [{"type": "analysis_error", "message": f"Issue detection failed: {e}", "severity": "low"}]

def detect_subaru_issues(datalog_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect Subaru-specific issues"""
    issues = []

    # Check for knock
    knock_columns = [col for col in datalog_df.columns if 'knock' in col.lower()]
    for knock_col in knock_columns:
        if knock_col in datalog_df.columns:
            knock_events = datalog_df[datalog_df[knock_col] > 0]
            if len(knock_events) > 0:
                issues.append({
                    "type": "knock",
                    "count": len(knock_events),
                    "severity": "high",
                    "message": f"Detected {len(knock_events)} knock events",
                    "column": knock_col
                })

    # Check for lean conditions (A/F Correction)
    af_columns = [col for col in datalog_df.columns if 'a/f correction' in col.lower()]
    for af_col in af_columns:
        if af_col in datalog_df.columns:
            lean_conditions = datalog_df[datalog_df[af_col] > 15]  # >15% correction
            if len(lean_conditions) > 0:
                issues.append({
                    "type": "lean_condition",
                    "count": len(lean_conditions),
                    "severity": "medium",
                    "message": f"Detected {len(lean_conditions)} lean conditions (>15% A/F correction)",
                    "column": af_col
                })

    # Check for high coolant temperature
    coolant_columns = [col for col in datalog_df.columns if 'coolant' in col.lower() and 'temp' in col.lower()]
    for coolant_col in coolant_columns:
        if coolant_col in datalog_df.columns:
            hot_conditions = datalog_df[datalog_df[coolant_col] > 220]  # >220°F
            if len(hot_conditions) > 0:
                issues.append({
                    "type": "overheating",
                    "count": len(hot_conditions),
                    "severity": "high",
                    "message": f"Detected {len(hot_conditions)} overheating conditions (>220°F)",
                    "column": coolant_col
                })

    return issues

def detect_hondata_issues(datalog_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect Hondata-specific issues"""
    issues = []

    # Check for knock (if available)
    knock_columns = [col for col in datalog_df.columns if 'knock' in col.lower()]
    for knock_col in knock_columns:
        knock_events = datalog_df[datalog_df[knock_col] > 0]
        if len(knock_events) > 0:
            issues.append({
                "type": "knock",
                "count": len(knock_events),
                "severity": "high",
                "message": f"Detected {len(knock_events)} knock events",
                "column": knock_col
            })

    # Check for lean AFR
    afr_columns = [col for col in datalog_df.columns if 'afr' in col.lower() or 'lambda' in col.lower()]
    for afr_col in afr_columns:
        if afr_col in datalog_df.columns:
            lean_conditions = datalog_df[datalog_df[afr_col] > 15.5]  # >15.5 AFR is lean
            if len(lean_conditions) > 0:
                issues.append({
                    "type": "lean_condition",
                    "count": len(lean_conditions),
                    "severity": "medium",
                    "message": f"Detected {len(lean_conditions)} lean conditions (AFR >15.5)",
                    "column": afr_col
                })

    return issues

def detect_generic_issues(datalog_df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Detect generic issues"""
    issues = []

    # Check for missing data
    missing_data_cols = datalog_df.columns[datalog_df.isnull().sum() > len(datalog_df) * 0.1]  # >10% missing
    for col in missing_data_cols:
        missing_count = datalog_df[col].isnull().sum()
        issues.append({
            "type": "missing_data",
            "count": missing_count,
            "severity": "low",
            "message": f"Column '{col}' has {missing_count} missing values",
            "column": col
        })

    return issues

def get_datalog_summary(datalog_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate a summary of the datalog

    Args:
        datalog_df: Parsed datalog DataFrame

    Returns:
        Dictionary containing datalog summary
    """
    try:
        summary = {
            "total_rows": len(datalog_df),
            "total_columns": len(datalog_df.columns),
            "platform": datalog_df.attrs.get('platform', 'Unknown'),
            "columns": list(datalog_df.columns),
            "numeric_columns": list(datalog_df.select_dtypes(include=[np.number]).columns),
            "missing_data": datalog_df.isnull().sum().to_dict(),
            "data_types": datalog_df.dtypes.astype(str).to_dict()
        }

        # Add time range if time column exists
        time_columns = [col for col in datalog_df.columns if 'time' in col.lower()]
        if time_columns:
            time_col = time_columns[0]
            if not datalog_df[time_col].isnull().all():
                summary["time_range"] = {
                    "start": float(datalog_df[time_col].min()),
                    "end": float(datalog_df[time_col].max()),
                    "duration": float(datalog_df[time_col].max() - datalog_df[time_col].min()),
                    "column": time_col
                }

        return summary

    except Exception as e:
        logger.error(f"Failed to generate datalog summary: {e}")
        return {"error": str(e)}

# Export main functions
__all__ = [
    'parse_datalog',
    'detect_issues', 
    'detect_platform_from_datalog',
    'get_datalog_summary',
    'DatalogParseError'
]
