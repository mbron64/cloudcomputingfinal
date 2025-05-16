# IoT Beehive Monitoring System

A cloud-based system for monitoring beehive health using audio analysis and machine learning. This project uses the MSPB dataset to train models that can detect various hive states (normal, swarming, distress) from audio recordings.

## Features

- Audio feature extraction (MFCCs, spectral centroid, zero-crossing rate)
- Machine learning model for behavior classification
- Cloud-based processing pipeline using GCP
- Real-time dashboard for monitoring
- SMS/Email alerts for critical events

# BuzzHive 🐝

[![Status](https://img.shields.io/badge/Status-Active-green.svg)](https://github.com/username/buzzhive)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/username/buzzhive/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-yellow.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![GCP](https://img.shields.io/badge/Cloud-GCP-blue.svg)](https://cloud.google.com/)

> An IoT-powered, cloud-based monitoring solution for beekeepers to remotely track and optimize bee colony health using machine learning and real-time analytics.

<p align="center">
  <img src="https://github.com/username/buzzhive/raw/main/assets/buzzhive-logo.png" alt="BuzzHive Logo" width="300">
</p>

## 🧠 Why BuzzHive?

Bee populations worldwide are declining at an alarming rate due to habitat loss, climate change, and pesticide use. As crucial pollinators, bees are essential to our ecosystem and food production. BuzzHive empowers beekeepers with technology to create optimal environments for bee colonies to thrive.

Unlike traditional beekeeping methods that rely on periodic manual inspections, BuzzHive provides:

- **Continuous monitoring** of hive conditions
- **Real-time alerts** for abnormal behavior detection
- **Data-driven insights** for optimizing colony health
- **Scalable architecture** for monitoring multiple hives across different locations

## ✨ Features

- 🔊 **Acoustic monitoring** to detect colony behavior states (normal, swarming, distress)
- 🌡️ **Environmental tracking** of temperature and humidity conditions
- ☣️ **Pesticide detection** in the surrounding area
- 📊 **Interactive dashboard** for real-time hive monitoring
- 📱 **SMS alerts** for critical events requiring intervention
- ☁️ **Cloud-based architecture** for reliable, scalable performance
- 🤖 **Machine learning powered** behavior analysis

## 🏗️ Architecture

BuzzHive uses a cloud-native architecture built on Google Cloud Platform:

```
                     ┌────────────────┐
                     │  IoT Sensors   │
                     │ (Audio, Temp,  │
                     │  Humidity)     │
                     └────────┬───────┘
                              │
                              ▼
┌────────────────┐    ┌───────────────┐    ┌────────────────┐
│  Google Cloud  │    │ Cloud Function │    │   Firestore    │
│    Storage     │◄───┤   (ML Model)   ├───►│   Database     │
│    Bucket      │    │                │    │                │
└────────────────┘    └───────┬───────┘    └─────┬──────────┘
                              │                  │
                              ▼                  │
                     ┌────────────────┐         │
                     │  Cloud Run     │◄────────┘
                     │  Dashboard     │
                     └───────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ SMS Alerts via  │
                    │     Twilio      │
                    └─────────────────┘
```

## 🚀 How It Works

1. **Data Collection**: IoT sensors collect acoustic, temperature, humidity, and pesticide data from beehives
2. **Data Storage**: WAV files and sensor readings are uploaded to Google Cloud Storage buckets
3. **ML Processing**: Cloud Functions process the data, extracting features like:
   - Mel-Frequency Cepstral Coefficients (MFCC)
   - Spectral centroid
   - Zero-crossing rate
4. **Behavior Analysis**: Random Forest model analyzes the data to determine hive state
5. **Data Storage**: Results are stored in Google Firestore (NoSQL database)
6. **Alerting**: Anomalies trigger SMS alerts via Twilio
7. **Visualization**: Cloud Run hosts an interactive dashboard displaying real-time conditions and historical data

## 💻 Technologies

- **Backend**: Python, Flask
- **Machine Learning**: Scikit-Learn, Joblib (Random Forest)
- **Audio Processing**: Librosa
- **Cloud Infrastructure**: Google Cloud Platform
  - Cloud Storage
  - Cloud Functions
  - Firestore
  - Cloud Run
- **Containerization**: Docker
- **Alerting**: Twilio SMS API
- **Frontend**: HTML, CSS, JavaScript, Bootstrap

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/username/buzzhive.git
cd buzzhive

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
export TWILIO_ACCOUNT_SID="your_account_sid"
export TWILIO_AUTH_TOKEN="your_auth_token"
```


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


## 🚢 Deployment

BuzzHive is designed to be deployed on Google Cloud Platform:

```bash
# Deploy the backend services
./deploy.sh
```

This script:
1. Creates a Google Cloud Storage bucket
2. Deploys the processing function
3. Sets up Twilio for alerts
4. Builds and pushes the dashboard Docker image
5. Deploys the dashboard to Cloud Run

## 👨‍💻 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👥 Team

- Michael - Backend development, Cloud infrastructure
- Saif - Cloud deployment, Backend configuration
- Allen - Frontend Dockerization, Dashboard deployment

## 🙏 Acknowledgements

- [MSPB dataset](https://www.kaggle.com/datasets/annajyang/beehive-sounds) - Longitudinal Multi-Sensor dataset with Phenotypic trait measurements from honey Bees
- Google Cloud Platform for providing cloud infrastructure
- Twilio for messaging services

---

<p align="center">
  Made with ❤️ for 🐝
</p>

