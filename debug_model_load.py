import joblib
import pickle
import os
import sys

print(f"Running on Python {sys.version}")

try:
    path = '/home/sebabte/canc/mymodel.pkl'
    print(f"Loading {path}...")
    model = joblib.load(path)
    print("SUCCESS: Model loaded with joblib.")
    # basic check
    if hasattr(model, 'summary'):
        print(model.summary())
except Exception as e:
    print(f"FAILURE: joblib load error: {e}")
    import traceback
    traceback.print_exc()
