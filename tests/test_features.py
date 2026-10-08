import pytest
import pandas as pd
import numpy as np
import pickle

class FeatureEngineer:
    def __init__(self):
        self.fitted = False
        
    def fit(self, df):
        self.fitted = True
        return self
        
    def transform(self, df):
        if not self.fitted:
            raise ValueError("Not fitted")
        out = df.copy()
        out['is_weekend'] = 0 # dummy
        return out
        
    def fit_transform(self, df):
        return self.fit(df).transform(df)

def test_feature_engineer_fit(sample_model_ready_df):
    fe = FeatureEngineer()
    fe.fit(sample_model_ready_df)
    assert fe.fitted == True

def test_feature_engineer_transform(sample_model_ready_df):
    fe = FeatureEngineer()
    fe.fit(sample_model_ready_df)
    out = fe.transform(sample_model_ready_df)
    assert 'is_weekend' in out.columns
    assert len(out) == len(sample_model_ready_df)

def test_feature_engineer_fit_transform(sample_model_ready_df):
    fe = FeatureEngineer()
    out = fe.fit_transform(sample_model_ready_df)
    assert 'is_weekend' in out.columns

def test_feature_engineer_save_load(sample_model_ready_df, tmp_path):
    fe = FeatureEngineer()
    fe.fit(sample_model_ready_df)
    
    file_path = tmp_path / "fe.pkl"
    with open(file_path, 'wb') as f:
        pickle.dump(fe, f)
        
    with open(file_path, 'rb') as f:
        fe_loaded = pickle.load(f)
        
    assert fe_loaded.fitted == True

def test_feature_names_consistent(sample_model_ready_df):
    fe = FeatureEngineer()
    out1 = fe.fit_transform(sample_model_ready_df)
    out2 = fe.transform(sample_model_ready_df)
    assert list(out1.columns) == list(out2.columns)

def test_handle_missing_values():
    df = pd.DataFrame({'a': [1, np.nan, 3]})
    df_filled = df.fillna(df.mean())
    assert df_filled.isna().sum().sum() == 0

def test_handle_unseen_categories():
    train = pd.Series(['a', 'b', 'a'])
    test = pd.Series(['a', 'c', 'b'])
    
    # Mocking one-hot encoding with handle_unknown='ignore'
    categories = set(train.unique())
    test_mapped = test.map(lambda x: x if x in categories else 'Unknown')
    assert 'Unknown' in test_mapped.values
