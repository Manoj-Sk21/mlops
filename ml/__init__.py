"""
ML package for Traffic Accident Severity Analytics.
"""
from .data import load_model_ready_data, split_data, get_class_distribution
from .features import FeatureEngineer, create_feature_pipeline
from .train import train_model, get_default_params, compute_class_weights
from .evaluate import evaluate_model, plot_confusion_matrix, plot_feature_importance, log_metrics_to_mlflow
from .inference import InferencePipeline
from .pipeline import run_training_pipeline

__all__ = [
    'load_model_ready_data',
    'split_data',
    'get_class_distribution',
    'FeatureEngineer',
    'create_feature_pipeline',
    'train_model',
    'get_default_params',
    'compute_class_weights',
    'evaluate_model',
    'plot_confusion_matrix',
    'plot_feature_importance',
    'log_metrics_to_mlflow',
    'InferencePipeline',
    'run_training_pipeline',
]
