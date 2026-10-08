import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder, StandardScaler
import joblib

class FeatureEngineer:
    def __init__(self):
        self.temporal = ['hour', 'day_of_week', 'month', 'is_weekend', 'is_rush_hour']
        self.weather = ['temperature', 'precipitation', 'wind_speed', 'rain', 'snowfall']
        self.road = ['speed_limit', 'number_of_vehicles', 'number_of_casualties']
        self.categorical_features = ['road_type', 'road_surface', 'light_conditions', 'weather_condition', 'urban_rural', 'junction_type', 'season']
        self.location = ['latitude', 'longitude']
        self.numerical_features = self.temporal + self.weather + self.road + self.location
        self.feature_columns = self.categorical_features + self.numerical_features
        
        self.label_encoders = {}
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.feature_names = []
        self.numerical_medians = {}
        self.categorical_modes = {}

    def fit(self, df: pd.DataFrame):
        for col in self.categorical_features:
            if col in df.columns:
                le = LabelEncoder()
                # Fit label encoder, handling unseen categories by appending 'unknown'
                unique_vals = list(df[col].astype(str).unique())
                unique_vals.append('unknown')
                le.fit(unique_vals)
                self.label_encoders[col] = le
                self.categorical_modes[col] = df[col].mode()[0] if not df[col].mode().empty else 'unknown'
                
        num_cols = [c for c in self.numerical_features if c in df.columns]
        if num_cols:
            self.scaler.fit(df[num_cols].fillna(df[num_cols].median()))
            for col in num_cols:
                self.numerical_medians[col] = df[col].median()
                
        self.feature_names = self.categorical_features + num_cols
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> tuple:
        if not self.is_fitted:
            raise ValueError("FeatureEngineer is not fitted yet.")
            
        df_transformed = pd.DataFrame()
        
        for col in self.categorical_features:
            if col in df.columns:
                # Handle unseen values
                le = self.label_encoders[col]
                vals = df[col].fillna(self.categorical_modes.get(col, 'unknown')).astype(str).values
                # Replace unseen with 'unknown'
                known_classes = set(le.classes_)
                vals = [x if x in known_classes else 'unknown' for x in vals]
                df_transformed[col] = le.transform(vals)
            else:
                df_transformed[col] = 0
                
        num_cols = [c for c in self.numerical_features if c in self.feature_names]
        if num_cols:
            num_data = df[num_cols].copy()
            for col in num_cols:
                num_data[col] = num_data[col].fillna(self.numerical_medians.get(col, 0))
            scaled = self.scaler.transform(num_data)
            for i, col in enumerate(num_cols):
                df_transformed[col] = scaled[:, i]
                
        # Reorder to match feature_names
        df_transformed = df_transformed[self.feature_names]
        return df_transformed.values, self.feature_names

    def fit_transform(self, df: pd.DataFrame) -> tuple:
        return self.fit(df).transform(df)

    def get_feature_importance_names(self) -> list:
        return self.feature_names

    def save(self, path: str) -> None:
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str):
        return joblib.load(path)

def create_feature_pipeline() -> FeatureEngineer:
    return FeatureEngineer()
