import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s | %(message)s')
logger = logging.getLogger('train_model')

# Model Paths
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")
MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest.joblib")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")

# Feature set for ML
FEATURE_COLS = [
    'time_diff', 'freq', 'byte_mean', 'byte_std', 
    'byte_min', 'byte_max', 'rolling_mean', 'rolling_std', 'entropy'
]

def train_model(df: pd.DataFrame):
    """
    ML Training Module: Fits scaler and Isolation Forest on cleaned data.
    Saves artifacts for production inference.
    """
    if df.empty:
        logger.error("Empty DataFrame provided for training.")
        return

    start_time = time.time()
    
    # 1. Feature Selection
    available_features = [c for c in FEATURE_COLS if c in df.columns]
    X = df[available_features].values
    logger.info(f"Starting training on {len(df)} rows with {len(available_features)} features.")

    # 2. Scaling
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # 3. Model Training
    model = IsolationForest(
        n_estimators=100,
        contamination=0.01,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_scaled)

    # 4. Save Artifacts
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    
    elapsed = time.time() - start_time
    logger.info(f"Training complete! Artifacts saved to {MODEL_DIR} (Time: {elapsed:.2f}s)")

if __name__ == "__main__":
    # Small test if run directly
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), "..", "data_processing"))
    from log_cleaner import load_all_logs
    from feature_engineering import build_features
    
    log_dirs = ["../../assets/log_files"] # Quick test
    df_raw = load_all_logs(log_dirs)
    if not df_raw.empty:
        df_feat = build_features(df_raw)
        train_model(df_feat)
