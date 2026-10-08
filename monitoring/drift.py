import os
import json
import numpy as np
import pandas as pd
from sqlalchemy import text
from typing import List, Dict

class DriftDetector:
    def __init__(self, engine=None):
        from . import get_db_engine
        self.engine = engine or get_db_engine()
        self.psi_threshold = float(os.getenv('DRIFT_PSI_THRESHOLD', '0.20'))

    def calculate_psi(self, reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
        """Population Stability Index calculation."""
        if len(reference) == 0 or len(current) == 0:
            return 0.0

        # Create bins based on reference data
        min_val = min(np.min(reference), np.min(current))
        max_val = max(np.max(reference), np.max(current))
        
        if min_val == max_val:
            return 0.0
            
        bins_arr = np.linspace(min_val, max_val, bins + 1)
        
        # Calculate distributions
        ref_hist, _ = np.histogram(reference, bins=bins_arr)
        curr_hist, _ = np.histogram(current, bins=bins_arr)
        
        # Convert to percentages
        ref_pct = ref_hist / len(reference)
        curr_pct = curr_hist / len(current)
        
        # Handle zero bins with small epsilon
        epsilon = 0.0001
        ref_pct = np.where(ref_pct == 0, epsilon, ref_pct)
        curr_pct = np.where(curr_pct == 0, epsilon, curr_pct)
        
        # Calculate PSI
        psi_values = (curr_pct - ref_pct) * np.log(curr_pct / ref_pct)
        psi = float(np.sum(psi_values))
        
        return psi

    def detect_feature_drift(self, reference_df: pd.DataFrame, current_df: pd.DataFrame, features: List[str]) -> List[Dict]:
        results = []
        for feature in features:
            if feature not in reference_df.columns or feature not in current_df.columns:
                continue
                
            ref_data = reference_df[feature].dropna()
            curr_data = current_df[feature].dropna()
            
            if pd.api.types.is_numeric_dtype(ref_data):
                psi = self.calculate_psi(ref_data.values, curr_data.values)
                is_drifted = psi > self.psi_threshold
                
                results.append({
                    'feature_name': feature,
                    'drift_type': 'feature_psi',
                    'metric_value': psi,
                    'threshold': self.psi_threshold,
                    'is_drifted': is_drifted,
                    'reference_distribution': None,
                    'current_distribution': None
                })
            else:
                # For categorical, calculate distribution PSI
                ref_counts = ref_data.value_counts(normalize=True)
                curr_counts = curr_data.value_counts(normalize=True)
                
                all_cats = set(ref_counts.index).union(set(curr_counts.index))
                
                ref_pct = np.array([ref_counts.get(c, 0) for c in all_cats])
                curr_pct = np.array([curr_counts.get(c, 0) for c in all_cats])
                
                epsilon = 0.0001
                ref_pct = np.where(ref_pct == 0, epsilon, ref_pct)
                curr_pct = np.where(curr_pct == 0, epsilon, curr_pct)
                
                psi = float(np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct)))
                
                results.append({
                    'feature_name': feature,
                    'drift_type': 'feature_categorical_psi',
                    'metric_value': psi,
                    'threshold': self.psi_threshold,
                    'is_drifted': psi > self.psi_threshold,
                    'reference_distribution': json.dumps(ref_counts.to_dict()),
                    'current_distribution': json.dumps(curr_counts.to_dict())
                })
                
        return results

    def detect_class_drift(self, reference_labels: pd.Series, current_labels: pd.Series) -> Dict:
        ref_counts = reference_labels.value_counts(normalize=True)
        curr_counts = current_labels.value_counts(normalize=True)
        
        all_cats = set(ref_counts.index).union(set(curr_counts.index))
        
        ref_pct = np.array([ref_counts.get(c, 0) for c in all_cats])
        curr_pct = np.array([curr_counts.get(c, 0) for c in all_cats])
        
        epsilon = 0.0001
        ref_pct = np.where(ref_pct == 0, epsilon, ref_pct)
        curr_pct = np.where(curr_pct == 0, epsilon, curr_pct)
        
        psi = float(np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct)))
        
        return {
            'drift_type': 'class',
            'metric_value': psi,
            'threshold': self.psi_threshold,
            'is_drifted': psi > self.psi_threshold,
            'reference_distribution': json.dumps(ref_counts.to_dict()),
            'current_distribution': json.dumps(curr_counts.to_dict())
        }

    def detect_location_drift(self, reference_df: pd.DataFrame, current_df: pd.DataFrame) -> Dict:
        if 'latitude' not in reference_df.columns or 'longitude' not in reference_df.columns:
            return {}
            
        lat_psi = self.calculate_psi(reference_df['latitude'].dropna().values, current_df['latitude'].dropna().values)
        lon_psi = self.calculate_psi(reference_df['longitude'].dropna().values, current_df['longitude'].dropna().values)
        
        max_psi = max(lat_psi, lon_psi)
        
        return {
            'drift_type': 'location',
            'metric_value': max_psi,
            'threshold': self.psi_threshold,
            'is_drifted': max_psi > self.psi_threshold,
            'reference_distribution': None,
            'current_distribution': None
        }

    def log_drift_results(self, results: List[Dict], run_id: str) -> None:
        if not results:
            return
            
        with self.engine.begin() as conn:
            for res in results:
                conn.execute(
                    text("""
                        INSERT INTO monitoring.drift_log 
                        (run_id, drift_type, feature_name, metric_name, metric_value, threshold, 
                         is_drifted, reference_distribution, current_distribution, created_at)
                        VALUES (:run_id, :drift_type, :feature_name, :metric_name, :metric_value, 
                                :threshold, :is_drifted, :ref_dist, :curr_dist, NOW())
                    """),
                    {
                        'run_id': run_id,
                        'drift_type': res.get('drift_type'),
                        'feature_name': res.get('feature_name', 'N/A'),
                        'metric_name': 'PSI',
                        'metric_value': res.get('metric_value'),
                        'threshold': res.get('threshold'),
                        'is_drifted': res.get('is_drifted'),
                        'ref_dist': res.get('reference_distribution'),
                        'curr_dist': res.get('current_distribution')
                    }
                )

    def run_all_drift_checks(self, reference_df: pd.DataFrame, current_df: pd.DataFrame, run_id: str = None) -> Dict:
        all_results = []
        
        # Feature drift
        features = [col for col in reference_df.columns if col not in ['id', 'severity', 'label']]
        feature_drifts = self.detect_feature_drift(reference_df, current_df, features)
        all_results.extend(feature_drifts)
        
        # Location drift
        loc_drift = self.detect_location_drift(reference_df, current_df)
        if loc_drift:
            loc_drift['feature_name'] = 'location'
            all_results.append(loc_drift)
            
        # Class drift (if labels present)
        if 'severity' in reference_df.columns and 'severity' in current_df.columns:
            class_drift = self.detect_class_drift(reference_df['severity'], current_df['severity'])
            class_drift['feature_name'] = 'target'
            all_results.append(class_drift)
            
        if run_id:
            self.log_drift_results(all_results, run_id)
            
        drifted_features = [r['feature_name'] for r in all_results if r.get('is_drifted')]
        
        return {
            'total_checks': len(all_results),
            'drifted_count': len(drifted_features),
            'drifted_features': drifted_features,
            'results': all_results
        }
