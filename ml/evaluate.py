import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report
)
import mlflow
import os

def evaluate_model(model, X_test, y_test, feature_names=None) -> dict:
    """
    Calculate and print all evaluation metrics.
    """
    y_test_mapped = y_test - 1 # map 1,2,3 to 0,1,2
    y_pred = model.predict(X_test)
    
    acc = accuracy_score(y_test_mapped, y_pred)
    macro_prec = precision_score(y_test_mapped, y_pred, average='macro', zero_division=0)
    macro_rec = recall_score(y_test_mapped, y_pred, average='macro', zero_division=0)
    macro_f1 = f1_score(y_test_mapped, y_pred, average='macro', zero_division=0)
    weighted_f1 = f1_score(y_test_mapped, y_pred, average='weighted', zero_division=0)
    
    per_class_prec = precision_score(y_test_mapped, y_pred, average=None, zero_division=0)
    per_class_rec = recall_score(y_test_mapped, y_pred, average=None, zero_division=0)
    per_class_f1 = f1_score(y_test_mapped, y_pred, average=None, zero_division=0)
    
    cm = confusion_matrix(y_test_mapped, y_pred)
    cr = classification_report(y_test_mapped, y_pred, target_names=['Fatal', 'Serious', 'Slight'], zero_division=0)
    
    # False Negative Rates for Fatal (0) and Serious (1)
    # FNR = FN / (FN + TP)
    fnr = {}
    for i, name in enumerate(['Fatal', 'Serious']):
        tp = cm[i, i]
        fn = np.sum(cm[i, :]) - tp
        fnr[name] = float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0

    metrics = {
        'accuracy': float(acc),
        'macro_precision': float(macro_prec),
        'macro_recall': float(macro_rec),
        'macro_f1': float(macro_f1),
        'weighted_f1': float(weighted_f1),
        'per_class_precision': {str(i): float(p) for i, p in enumerate(per_class_prec)},
        'per_class_recall': {str(i): float(r) for i, r in enumerate(per_class_rec)},
        'per_class_f1': {str(i): float(f) for i, f in enumerate(per_class_f1)},
        'confusion_matrix': cm.tolist(),
        'classification_report': cr,
        'false_negative_rate': fnr
    }
    
    print("=== Evaluation Metrics ===")
    print(f"Accuracy: {acc:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")
    print("Classification Report:")
    print(cr)
    
    return metrics

def plot_confusion_matrix(cm, class_names=['Fatal', 'Serious', 'Slight']) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=class_names, yticklabels=class_names, ax=ax)
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.title('Confusion Matrix')
    plt.tight_layout()
    return fig

def plot_feature_importance(model, feature_names, top_n=20) -> plt.Figure:
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:top_n]
    
    top_features = [feature_names[i] for i in indices]
    top_importances = importances[indices]
    
    fig, ax = plt.subplots(figsize=(10, 8))
    sns.barplot(x=top_importances, y=top_features, ax=ax, palette='viridis')
    plt.title(f'Top {top_n} Feature Importances')
    plt.xlabel('Importance')
    plt.tight_layout()
    return fig

def log_metrics_to_mlflow(metrics, params, model, feature_engineer, artifacts_dir) -> None:
    os.makedirs(artifacts_dir, exist_ok=True)
    
    mlflow.log_params(params)
    
    flat_metrics = {
        'accuracy': metrics['accuracy'],
        'macro_precision': metrics['macro_precision'],
        'macro_recall': metrics['macro_recall'],
        'macro_f1': metrics['macro_f1'],
        'weighted_f1': metrics['weighted_f1'],
        'fnr_fatal': metrics['false_negative_rate'].get('Fatal', 0),
        'fnr_serious': metrics['false_negative_rate'].get('Serious', 0)
    }
    mlflow.log_metrics(flat_metrics)
    
    # Save artifacts locally first
    cm_path = os.path.join(artifacts_dir, 'confusion_matrix.png')
    fig_cm = plot_confusion_matrix(np.array(metrics['confusion_matrix']))
    fig_cm.savefig(cm_path)
    plt.close(fig_cm)
    mlflow.log_artifact(cm_path)
    
    if hasattr(feature_engineer, 'feature_names') and feature_engineer.feature_names:
        fi_path = os.path.join(artifacts_dir, 'feature_importance.png')
        fig_fi = plot_feature_importance(model, feature_engineer.feature_names)
        fig_fi.savefig(fi_path)
        plt.close(fig_fi)
        mlflow.log_artifact(fi_path)
        
    cr_path = os.path.join(artifacts_dir, 'classification_report.txt')
    with open(cr_path, 'w') as f:
        f.write(metrics['classification_report'])
    mlflow.log_artifact(cr_path)
    
    fe_path = os.path.join(artifacts_dir, 'feature_engineer.joblib')
    feature_engineer.save(fe_path)
    mlflow.log_artifact(fe_path)
    
    mlflow.xgboost.log_model(model, 'model')
