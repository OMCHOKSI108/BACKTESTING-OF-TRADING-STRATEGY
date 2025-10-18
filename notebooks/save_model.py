#!/usr/bin/env python3
"""
Extract and save the trained Cerberus model from the notebook
"""

import os
import sys
sys.path.append('..')

# Import the model from the notebook's kernel
# This assumes the notebook has been run and model_relaxed is available
try:
    # Try to load from the notebook's saved variables
    import pickle

    # For now, let's create a placeholder - in practice you'd extract from the running notebook
    print("⚠️  This script needs to be run from within the notebook environment")
    print("Please run the following code in the cerberus_impulse_model.ipynb notebook:")

    print("""
# Save the trained model
import os
os.makedirs('../models', exist_ok=True)
model_relaxed.save_model('../models/cerberus_model_relaxed.txt')
print("✅ Model saved to ../models/cerberus_model_relaxed.txt")
""")

except Exception as e:
    print(f"Error: {e}")

print("After saving the model, you can use the signal generator:")
print("python ../cerberus_signal_generator.py --csv path/to/your/data.csv --symbol YOUR_SYMBOL")