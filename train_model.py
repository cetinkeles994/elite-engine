import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

DATA_FILE = "training_data.csv"
MODEL_FILE = "model.pkl"
ENCODER_FILE = "encoder.pkl"

def train():
    print("🚀 Starting AI Training Session...")
    
    if not os.path.exists(DATA_FILE):
        print(f"❌ Error: {DATA_FILE} not found!")
        return

    # 1. Load Data
    try:
        df = pd.read_csv(DATA_FILE)
        print(f"✅ Loaded {len(df)} matches from history.")
    except Exception as e:
        print(f"❌ Failed to load CSV: {e}")
        return

    # 2. Preprocessing
    # We need to convert categorical text (League) into numbers
    # And ensure our target (won/lost) is 1/0
    
    # Target Variable
    df = df[df['result'].isin(['won', 'lost'])] # Filter valid results
    df['target'] = df['result'].apply(lambda x: 1 if x == 'won' else 0)
    
    # Feature Engineering
    # Input Features: League, Home Odds, Away Odds, Confidence
    
    # Initialize Label Encoder for Leagues (convert "Premier League" -> 1, "La Liga" -> 2...)
    le = LabelEncoder()
    df['league_code'] = le.fit_transform(df['league'])
    
    # Select Features for Training
    X = df[['league_code', 'home_odds', 'away_odds', 'confidence']]
    y = df['target']
    
    print(f"📊 Training on {len(df)} validated samples...")
    
    # 3. Train Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 4. Model Initialization (Random Forest)
    # n_estimators=100 (100 trees), max_depth=10 (prevent overfitting)
    rf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    
    # 5. Training
    rf.fit(X_train, y_train)
    
    # 6. Evaluation
    y_pred = rf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    
    print("\n------------------------------------------------")
    print(f"🏆 MODEL ACCURACY: {acc * 100:.2f}%")
    print("------------------------------------------------")
    print(classification_report(y_test, y_pred))
    
    # 7. Save Artifacts
    joblib.dump(rf, MODEL_FILE)
    joblib.dump(le, ENCODER_FILE)
    print(f"💾 Model saved to {MODEL_FILE}")
    print(f"💾 Encoder saved to {ENCODER_FILE}")
    print("\n✅ AI System is ready for integration!")

if __name__ == "__main__":
    train()
