#!/bin/bash
pip install --upgrade pip setuptools wheel
pip install numpy==1.23.5
pip install scipy==1.10.1
pip install scikit-learn==1.2.2 --no-build-isolation
pip install joblib==1.2.0
pip install -r requirements.txt