import pandas as pd
import numpy as np
from datetime import datetime
from ingestion.ingestion_utils import log_data_quality, log_rejected_record, log_validation_summary

class DataQualityValidator:
    def __init__(self, engine, run_id):
        self.engine = engine
        self.run_id = run_id
        
    def validate_accidents(self, df: pd.DataFrame):
        df_copy = df.copy()
        rejected_indices = set()
        results = []
        
        # 1. check_missing_values
        crit_cols = ['accident_index', 'date', 'latitude', 'longitude', 'accident_severity']
        missing_mask = df_copy[crit_cols].isnull().any(axis=1)
        missing_count = missing_mask.sum()
        if missing_count > 0:
            rejected_indices.update(df_copy[missing_mask].index)
            log_data_quality(self.engine, self.run_id, "Missing Critical Values", "Completeness", "accidents", ", ".join(crit_cols), "FAILED", f"{missing_count} rows missing critical data", int(missing_count))
            
        # 2. check_duplicate_ids
        dup_mask = df_copy.duplicated(subset=['accident_index'], keep=False)
        dup_count = dup_mask.sum()
        if dup_count > 0:
            rejected_indices.update(df_copy[dup_mask].index)
            log_data_quality(self.engine, self.run_id, "Duplicate IDs", "Uniqueness", "accidents", "accident_index", "FAILED", f"{dup_count} duplicate rows", int(dup_count))
            
        # 3. check_invalid_coordinates
        # UK Bounding Box roughly
        lat_valid = df_copy['latitude'].between(49.0, 61.0) | df_copy['latitude'].isna()
        lon_valid = df_copy['longitude'].between(-8.0, 2.0) | df_copy['longitude'].isna()
        invalid_coord_mask = ~(lat_valid & lon_valid)
        invalid_coord_count = invalid_coord_mask.sum()
        if invalid_coord_count > 0:
            rejected_indices.update(df_copy[invalid_coord_mask].index)
            log_data_quality(self.engine, self.run_id, "Invalid Coordinates", "Validity", "accidents", "latitude/longitude", "FAILED", "Coordinates outside UK bounds", int(invalid_coord_count))
            
        # 4. check_invalid_dates
        try:
            dates = pd.to_datetime(df_copy['date'], format='%d/%m/%Y', errors='coerce')
            invalid_date_mask = dates.isna() | (dates.dt.year < 2000) | (dates.dt.year > 2030)
            invalid_date_count = invalid_date_mask.sum()
            if invalid_date_count > 0:
                rejected_indices.update(df_copy[invalid_date_mask].index)
                log_data_quality(self.engine, self.run_id, "Invalid Dates", "Validity", "accidents", "date", "FAILED", "Dates invalid or out of range", int(invalid_date_count))
        except Exception as e:
            pass
            
        # Prepare valid and rejected
        rejected_df = df_copy.loc[list(rejected_indices)]
        valid_df = df_copy.drop(index=list(rejected_indices))
        
        # Log summary
        log_validation_summary(self.engine, self.run_id, "Accidents Validation", 4, 4 - (len(rejected_indices)>0), (len(rejected_indices)>0), len(df_copy), len(rejected_df))
        
        return valid_df, rejected_df, results
        
    def validate_vehicles(self, df: pd.DataFrame):
        # Simplified validation for vehicles
        rejected_indices = set()
        
        missing_mask = df['accident_index'].isnull()
        if missing_mask.sum() > 0:
            rejected_indices.update(df[missing_mask].index)
            
        valid_df = df.drop(index=list(rejected_indices))
        rejected_df = df.loc[list(rejected_indices)]
        log_validation_summary(self.engine, self.run_id, "Vehicles Validation", 1, 1, 0, len(df), len(rejected_df))
        
        return valid_df, rejected_df, []
        
    def validate_casualties(self, df: pd.DataFrame):
        # Simplified validation for casualties
        rejected_indices = set()
        
        missing_mask = df['accident_index'].isnull()
        if missing_mask.sum() > 0:
            rejected_indices.update(df[missing_mask].index)
            
        valid_df = df.drop(index=list(rejected_indices))
        rejected_df = df.loc[list(rejected_indices)]
        log_validation_summary(self.engine, self.run_id, "Casualties Validation", 1, 1, 0, len(df), len(rejected_df))
        
        return valid_df, rejected_df, []

    def run_all_validations(self, accidents_df, vehicles_df, casualties_df):
        acc_valid, acc_rej, acc_res = self.validate_accidents(accidents_df)
        veh_valid, veh_rej, veh_res = self.validate_vehicles(vehicles_df)
        cas_valid, cas_rej, cas_res = self.validate_casualties(casualties_df)
        
        return {
            'accidents': {'valid': acc_valid, 'rejected': acc_rej},
            'vehicles': {'valid': veh_valid, 'rejected': veh_rej},
            'casualties': {'valid': cas_valid, 'rejected': cas_rej}
        }
