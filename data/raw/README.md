# Datasets Repository

## Available Datasets

### 1. PaySim Synthetic Financial Fraud
- **File**: `paysim.csv`
- **Size**: 186 MB
- **Records**: 6.3M transactions
- **Features**: step, type, amount, nameOrig, oldbalanceOrg, newbalanceOrig, nameDest, oldbalanceDest, newbalanceDest, isFraud, isFlaggedFraud

### 2. Credit Card Fraud Detection (ULB)
- **File**: `creditcard.csv`
- **Size**: 69 MB
- **Records**: 284K transactions
- **Features**: Time, V1-V28, Amount, Class

## Download Instructions

### PaySim Dataset
```bash
# Download from Kaggle (requires kaggle API)
kaggle datasets download -d ealaxli/paysim1 -p data/raw/
unzip data/raw/paysim1.zip -d data/raw/
mv data/raw/PS_20174392719_1491204439457_log.csv data/raw/paysim.csv
```

### Credit Card Fraud Dataset
```bash
# Download from Kaggle
kaggle datasets download -d mlg-ulb/creditcardfraud -p data/raw/
unzip data/raw/creditcardfraud.zip -d data/raw/
```

## Usage

Once downloaded, the datasets will be automatically used by:
- Model training: `POST /model/retrain`
- Feature extraction: DataProcessor
- Real-time predictions: PredictionService
