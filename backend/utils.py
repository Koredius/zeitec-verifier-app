import hashlib
import os
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename
from typing import Tuple, Dict, List, Any


def allowed_file(filename: str, allowed_extensions: set) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def calculate_sha256(data: str) -> str:
    """Calculate SHA256 hash of a string"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read file in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def calculate_audit_trail_id(device_id: str, timestamp: str, kwh: float) -> str:
    """
    Calculate auditTrailId = SHA256(deviceId + timestamp + kWh)
    This is the core deduplication mechanism
    """
    data = f"{device_id}{timestamp}{kwh}"
    return calculate_sha256(data)


def save_uploaded_file(file, upload_folder: str, subfolder: str = '') -> Tuple[str, str, int]:
    """
    Save uploaded file and return (file_path, file_hash, file_size)
    """
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{timestamp}_{filename}"
    
    # Create subfolder if specified
    if subfolder:
        folder_path = os.path.join(upload_folder, subfolder)
    else:
        folder_path = upload_folder
        
    os.makedirs(folder_path, exist_ok=True)
    
    file_path = os.path.join(folder_path, unique_filename)
    file.save(file_path)
    
    # Calculate hash and size
    file_hash = calculate_file_hash(file_path)
    file_size = os.path.getsize(file_path)
    
    return file_path, file_hash, file_size


def validate_device_registry_csv(file_path: str, required_columns: List[str], max_capacity_kw: float) -> Dict[str, Any]:
    """
    Validate Device Registry CSV file
    Returns: {
        'valid': bool,
        'errors': List[str],
        'data': pd.DataFrame or None,
        'summary': Dict
    }
    """
    result = {
        'valid': True,
        'errors': [],
        'data': None,
        'summary': {}
    }
    
    try:
        # Read CSV
        df = pd.read_csv(file_path)
        result['summary']['total_rows'] = len(df)
        
        # Check required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            result['valid'] = False
            result['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
            return result
        
        # Validate capacity (≤250 kW requirement)
        if 'capacityKW' in df.columns:
            over_capacity = df[df['capacityKW'] > max_capacity_kw]
            if len(over_capacity) > 0:
                result['valid'] = False
                result['errors'].append(
                    f"{len(over_capacity)} devices exceed maximum capacity of {max_capacity_kw} kW"
                )
                result['summary']['over_capacity_devices'] = over_capacity['deviceId'].tolist()
        
        # Check for duplicates
        if 'deviceId' in df.columns and 'facilityId' in df.columns:
            duplicates = df[df.duplicated(subset=['deviceId', 'facilityId'], keep=False)]
            if len(duplicates) > 0:
                result['valid'] = False
                result['errors'].append(
                    f"{len(duplicates)} duplicate device-facility combinations found"
                )
        
        # Validate country
        if 'country' in df.columns:
            allowed_countries = ['Nigeria', 'Benin', 'Ghana', 'Kenya', 'South Africa']
            invalid_countries = df[~df['country'].isin(allowed_countries)]
            if len(invalid_countries) > 0:
                result['valid'] = False
                result['errors'].append(
                    f"{len(invalid_countries)} devices have invalid country codes"
                )
        
        result['data'] = df
        result['summary']['unique_devices'] = df['deviceId'].nunique() if 'deviceId' in df.columns else 0
        
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"CSV parsing error: {str(e)}")
    
    return result


def validate_issuance_period_csv(file_path: str, required_columns: List[str]) -> Dict[str, Any]:
    """
    Validate Issuance Period CSV file
    Returns: {
        'valid': bool,
        'errors': List[str],
        'data': pd.DataFrame or None,
        'summary': Dict,
        'audit_trail_ids': List[str]
    }
    """
    result = {
        'valid': True,
        'errors': [],
        'data': None,
        'summary': {},
        'audit_trail_ids': []
    }
    
    try:
        # Read CSV
        df = pd.read_csv(file_path)
        result['summary']['total_rows'] = len(df)
        
        # Check required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            result['valid'] = False
            result['errors'].append(f"Missing required columns: {', '.join(missing_columns)}")
            return result
        
        # Parse timestamp
        try:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"Invalid timestamp format: {str(e)}")
            return result
        
        # Validate kWh values (must be positive)
        if 'kWh' in df.columns:
            negative_kwh = df[df['kWh'] < 0]
            if len(negative_kwh) > 0:
                result['valid'] = False
                result['errors'].append(f"{len(negative_kwh)} rows have negative kWh values")
            
            # Calculate total kWh
            result['summary']['total_kwh'] = float(df['kWh'].sum())
        
        # Check for timestamp gaps (for hourly data)
        if 'timestamp' in df.columns:
            df_sorted = df.sort_values('timestamp')
            time_diffs = df_sorted['timestamp'].diff()
            
            # Check if any gaps exceed 2 hours (allowing some tolerance)
            large_gaps = time_diffs[time_diffs > pd.Timedelta(hours=2)]
            if len(large_gaps) > 0:
                result['errors'].append(
                    f"Warning: {len(large_gaps)} time gaps exceeding 2 hours detected"
                )
        
        # Collect audit trail IDs (or calculate if not present)
        if 'auditTrailId' in df.columns:
            result['audit_trail_ids'] = df['auditTrailId'].tolist()
        else:
            # Calculate audit trail IDs
            audit_trail_ids = []
            for _, row in df.iterrows():
                audit_id = calculate_audit_trail_id(
                    str(row['deviceId']),
                    str(row['timestamp']),
                    float(row['kWh'])
                )
                audit_trail_ids.append(audit_id)
            result['audit_trail_ids'] = audit_trail_ids
            df['auditTrailId'] = audit_trail_ids
        
        result['data'] = df
        result['summary']['unique_devices'] = df['deviceId'].nunique() if 'deviceId' in df.columns else 0
        result['summary']['period_start'] = df['timestamp'].min().isoformat() if 'timestamp' in df.columns else None
        result['summary']['period_end'] = df['timestamp'].max().isoformat() if 'timestamp' in df.columns else None
        
    except Exception as e:
        result['valid'] = False
        result['errors'].append(f"CSV parsing error: {str(e)}")
    
    return result


def check_duplicates(audit_trail_ids: List[str], existing_audit_trail_ids: List[str]) -> Dict[str, Any]:
    """
    Check for duplicate auditTrailIds
    Returns: {
        'has_duplicates': bool,
        'duplicate_count': int,
        'duplicate_ids': List[str]
    }
    """
    duplicates = set(audit_trail_ids) & set(existing_audit_trail_ids)
    
    return {
        'has_duplicates': len(duplicates) > 0,
        'duplicate_count': len(duplicates),
        'duplicate_ids': list(duplicates)
    }


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def create_verifier_checklist() -> Dict[str, bool]:
    """Create default verifier checklist"""
    return {
        'device_metadata_matches': False,
        'owner_declaration_valid': False,
        'supporting_docs_complete': False,
        'data_granularity_correct': False,
        'energy_values_reasonable': False,
        'no_timestamp_gaps': False,
        'measurement_tier_declared': False,
        'device_scope_confirmed': False,
        'grouping_keys_consistent': False,
        'no_dedupe_collisions': False
    }
