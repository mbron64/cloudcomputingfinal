# IoT Beehive Monitoring System

A cloud-based system for monitoring beehive health using audio analysis and machine learning. This project uses the MSPB dataset to train models that can detect various hive states (normal, swarming, distress) from audio recordings.

## Features

- Audio feature extraction (MFCCs, spectral centroid, zero-crossing rate)
- Machine learning model for behavior classification
- Cloud-based processing pipeline using GCP
- Real-time dashboard for monitoring
- SMS/Email alerts for critical events

## Project Structure

```
.
├── src/
│   ├── data/           # Data processing and loading
│   ├── models/         # ML model training and inference
│   └── utils/          # Utility functions
├── tests/              # Test files
├── config/             # Configuration files
└── requirements.txt    # Project dependencies
```

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up GCP credentials:
- Create a service account and download the JSON key
- Set the environment variable:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
```

4. Configure alerting (optional):
- Set up Twilio account and get credentials
- Set up SendGrid account and get API key
- Add credentials to environment variables or config file

## Usage

### Training the Model

```bash
python src/models/trainer.py
```

### Running the Dashboard

```bash
streamlit run src/dashboard/app.py
```

### Deploying to GCP

1. Deploy Cloud Function:
```bash
gcloud functions deploy process_audio \
    --runtime python310 \
    --trigger-resource my-beehive-audio-bucket \
    --trigger-event google.storage.object.finalize \
    --source . \
    --entry-point process_audio
```

2. Deploy Dashboard:
```bash
gcloud run deploy beehive-dashboard \
    --source . \
    --platform managed
```

## Development

- Run tests: `pytest`
- Format code: `black .`
- Lint code: `flake8`

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request
# cloudcomputingfinal
