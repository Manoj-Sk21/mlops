import os
import pandas as pd
import logging
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

def load_model_ready_data(engine=None) -> pd.DataFrame:
    """
    Load data from model_ready.accident_features table.
    If table empty or DB unavailable, try loading from data/model_ready/accident_features.csv
    """
    df = None
    if engine is not None:
        try:
            query = "SELECT * FROM model_ready.accident_features"
            df = pd.read_sql(query, engine)
            if df.empty:
                logger.warning("Table model_ready.accident_features is empty.")
                df = None
        except Exception as e:
            logger.warning(f"Failed to load from DB: {e}")
            df = None
            
    if df is None:
        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'model_ready', 'accident_features.csv')
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"Loaded data from {csv_path}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Could not find fallback data at {csv_path}")
            
    logger.info(f"Data shape: {df.shape}")
    dist = get_class_distribution(df)
    logger.info(f"Class distribution: {dist}")
    return df

def split_data(df: pd.DataFrame, test_size: float = 0.15, val_size: float = 0.15) -> tuple:
    """
    Chronological split (sort by year, month, day_of_week)
    Training: earliest 70%
    Validation: next 15%
    Test: latest 15%
    """
    # Sort chronologically
    df_sorted = df.sort_values(by=['year', 'month', 'day_of_week']).reset_index(drop=True)
    
    n = len(df_sorted)
    train_end = int(n * (1.0 - test_size - val_size))
    val_end = int(n * (1.0 - test_size))
    
    train_df = df_sorted.iloc[:train_end].copy()
    val_df = df_sorted.iloc[train_end:val_end].copy()
    test_df = df_sorted.iloc[val_end:].copy()
    
    logger.info(f"Split sizes: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    
    # Very basic verification
    if not train_df.empty and not val_df.empty:
        train_max_year = train_df['year'].max()
        val_min_year = val_df['year'].min()
        logger.info(f"Train ends at year {train_max_year}, Val starts at year {val_min_year}")
        
    return train_df, val_df, test_df

def get_class_distribution(df: pd.DataFrame, target_col: str = 'severity') -> dict:
    """
    Count and percentage per class
    """
    if target_col not in df.columns:
        return {}
        
    counts = df[target_col].value_counts()
    percentages = df[target_col].value_counts(normalize=True) * 100
    
    dist = {}
    for cls in counts.index:
        dist[cls] = {'count': int(counts[cls]), 'percentage': float(percentages[cls])}
        print(f"Class {cls}: {counts[cls]} ({percentages[cls]:.2f}%)")
        
    return dist
