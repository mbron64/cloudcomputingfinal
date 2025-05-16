# 🐝 Cloud Based Software Environment for IoT Beehive Monitoring

<p align="center">
  <img src="docs/beehive-monitoring-logo.png" alt="Beehive Monitoring Logo" width="300">
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/Status-Active-green.svg" alt="Status"></a>
  <a href="#license"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <a href="#"><img src="https://img.shields.io/badge/Python-3.9+-yellow.svg" alt="Python"></a>
  <a href="#docker-deployment"><img src="https://img.shields.io/badge/Docker-Enabled-blue.svg" alt="Docker"></a>
  <a href="#google-cloud-platform-deployment"><img src="https://img.shields.io/badge/Cloud-GCP-blue.svg" alt="GCP"></a>
</p>

> A cloud-based IoT system for monitoring beehive health using audio analysis and machine learning.
> Binghamton University CS552 Cloud Computing Spring 2025
> Michael Bronikowski, Allen Domingo, and Saif Ali


## 📋 Overview

This project implements a complete end-to-end IoT solution for beekeepers to monitor the health and behavior of their beehives using audio analysis. The system consists of:

1. **IoT Devices**: Simulated bee monitoring devices that collect audio data
2. **Cloud Functions**: Process incoming data using machine learning
3. **Firestore Database**: Store processed events and predictions
4. **Dashboard**: Real-time monitoring of beehive conditions

## ✨ Features

- 🔊 **Acoustic monitoring** to detect colony behavior states (normal, swarming, distress)
- 🌡️ **Environmental tracking** of temperature and humidity conditions
- 📊 **Interactive dashboard** for real-time hive monitoring
- ⚠️ **Automated alerts** for abnormal behavior detection
- ☁️ **Cloud-based architecture** for reliable, scalable performance
- 🤖 **Machine learning powered** behavior analysis

## 🏗️ System Architecture

<p align="center">
  <img src="docs/architecture.png" alt="Beehive Monitoring Architecture">
</p>

The system follows a serverless architecture:

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

1. **IoT Devices**: Collect audio data from beehives
2. **Cloud Storage**: Store raw data
3. **Cloud Functions**: Process data using ML
4. **Firestore**: Store processed results
5. **Dashboard**: Visualize insights

## 🚀 Quick Start

### Prerequisites

Before you begin, ensure you have:
- Python 3.9+ installed
- pip (Python package manager)
- git
- Docker (optional, for containerized deployment)
- Google Cloud SDK (optional, for cloud deployment)

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd beehive-monitoring
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the pipeline with specific components**:

   You can run individual components of the pipeline:
   ```bash
   # For data exploration
   ./run_pipeline.sh --explore
   
   # For model training
   ./run_pipeline.sh --train
   
   # For IoT simulation
   ./run_pipeline.sh --simulate
   
   # For the dashboard
   ./run_pipeline.sh --dashboard
   ```
   
   Or run everything at once:
   ```bash
   ./run_pipeline.sh
   ```

4. **Running the dashboard directly**:
   
   For the best experience running just the dashboard:
   ```bash
   ./run_dashboard.sh
   ```
   
   This ensures the dashboard runs with all required dependencies in the virtual environment.

5. **View the dashboard**:
   
   Open `http://localhost:8501` in your browser

### Docker Deployment

For containerized deployment, use Docker Compose:

```bash
docker-compose up
```

This will start:
- Dashboard service
- Data simulation service (for testing)

## 🔧 Troubleshooting

If you encounter issues:

1. **Missing packages**: Make sure you're using the virtual environment
   ```bash
   source venv/bin/activate
   ```

2. **Dashboard errors**: Use the provided script instead of running Streamlit directly
   ```bash
   ./run_dashboard.sh
   ```
   
   If you encounter errors with packages, try:
   ```bash
   ./install_dashboard_deps.sh
   ```

3. **Google Cloud errors**: For local development, ensure the dashboard is in demo mode (default). To use cloud features:
   ```bash
   gcloud auth application-default login
   ./run_pipeline.sh --cloud
   ```

4. **Installation issues**: If you face dependency issues, try:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

## ☁️ Google Cloud Platform Deployment

### Prerequisites

1. Google Cloud Platform account
2. `gcloud` CLI installed and configured
3. Project created in GCP with billing enabled
4. Required APIs enabled:
   - Cloud Functions
   - Cloud Storage
   - Firestore
   - Cloud Run (for dashboard)

### Deployment Steps

The easiest way to deploy the entire system is using the provided deployment script:

```bash
# Make the script executable
chmod +x deploy_cloud.sh

# Deploy the system
./deploy_cloud.sh
```

This will:
1. Configure your GCP project
2. Create necessary resources (buckets, databases)
3. Deploy the cloud function
4. Deploy the dashboard to Cloud Run
5. Set up permissions
6. Print the URL of your deployed dashboard

### Testing Cloud Deployment (Dry Run)

You can test the cloud deployment process without creating resources:

```bash
chmod +x test_cloud_deploy.sh
./test_cloud_deploy.sh
```

This simulates the deployment process and validates your configuration.

### Manual Deployment

If you prefer to deploy components individually:

#### 1. Set up environment

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export BUCKET_NAME="${PROJECT_ID}-beehive-data"
```

#### 2. Create Cloud Storage bucket

```bash
gsutil mb -l $REGION gs://$BUCKET_NAME
```

#### 3. Deploy Cloud Function

```bash
# Create a service account
export SERVICE_ACCOUNT="beehive-processor-sa"
gcloud iam service-accounts create $SERVICE_ACCOUNT

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# Deploy function
gcloud functions deploy beehive-processor \
  --gen2 \
  --region=$REGION \
  --runtime=python39 \
  --source=cloud_function \
  --entry-point=process_audio \
  --trigger-event=google.storage.object.finalize \
  --trigger-resource=$BUCKET_NAME \
  --service-account=${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com
```

#### 4. Deploy Dashboard to Cloud Run

```bash
# Build container
gcloud builds submit --tag gcr.io/$PROJECT_ID/beehive-dashboard

# Deploy to Cloud Run
gcloud run deploy beehive-dashboard \
  --image=gcr.io/$PROJECT_ID/beehive-dashboard \
  --platform=managed \
  --region=$REGION \
  --allow-unauthenticated
```

## 🐳 Docker Images

The project includes Docker configurations for all components:

### Dashboard Image

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ /app/src/
COPY scripts/ /app/scripts/
RUN mkdir -p /app/models /app/data /app/outputs
EXPOSE 8080
ENTRYPOINT ["streamlit", "run", "src/dashboard/app.py", "--server.port=8080", "--server.address=0.0.0.0"]
```

### Cloud Function Image

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY cloud_function/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY models/ /app/models/
COPY cloud_function/ /app/
ENV PORT=8080
ENV FUNCTION_TARGET=process_audio
CMD ["functions-framework", "--target", "${FUNCTION_TARGET}", "--port", "${PORT}"]
```

## 🧩 Project Structure

```
├── data/                # Raw sensor data
├── config/              # Configuration files
├── docker/              # Docker configuration files
│   ├── Dockerfile.dashboard
│   └── Dockerfile.function
├── models/              # Trained ML models
├── outputs/             # Generated plots and visualizations
├── processed_data/      # Preprocessed datasets
├── scripts/             # Utility scripts
│   ├── explore_data.py
│   ├── simulate_iot_uploads.py
│   └── train_basic_model.py
├── simulation_output/   # Simulated IoT device data
├── src/                 # Source code
│   ├── cloud/           # Cloud function code
│   ├── dashboard/       # Streamlit dashboard
│   └── data/            # Data processing modules
├── tests/               # Test files
├── cloud_function/      # Deployed cloud function code
├── docker-compose.yml   # Docker Compose configuration
├── Dockerfile           # Main Dockerfile
├── deploy_cloud.sh      # GCP deployment script
├── deploy.sh            # Deployment helper script
├── install_dashboard_deps.sh # Dashboard dependency installer
├── test_cloud_deploy.sh # Cloud deployment test script
├── test_docker.sh       # Docker test script
├── run_dashboard.sh     # Dashboard launcher script
├── requirements.txt     # Python dependencies
└── run_pipeline.sh      # Main pipeline script
```

## 🧪 Development

### Running Tests

```bash
pytest
```

### Local Development with Cloud Services

For local development against cloud services:

1. Set up GCP credentials:
   ```bash
   gcloud auth application-default login
   ```

2. Run the pipeline in cloud mode:
   ```bash
   ./run_pipeline.sh --cloud
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔍 Additional Information

### Pipeline Components

#### 1. Data Processing
Analyzes sensor data and annotations, generating visualizations to understand the acoustic patterns of beehives.

#### 2. Model Training
Trains a Random Forest classifier to identify bee behaviors.

#### 3. Cloud Deployment
- **Storage**: Cloud Storage for raw audio files
- **Processing**: Cloud Functions for audio analysis
- **Database**: Firestore for processed results
- **Dashboard**: Cloud Run for interactive web UI
- **Notifications**: Pub/Sub for alerting

#### 4. Dashboard
A Streamlit-based dashboard deployed to Cloud Run for:
- Visualizing real-time bee behavior
- Tracking behavior changes over time
- Alerting on abnormal behavior

### Dashboard Modes

The dashboard supports two operational modes:
- **Demo Mode**: Uses simulated data (default for local running)
- **Cloud Mode**: Connects to Firestore to display real data from IoT devices

### Handling Large Data Files

This project uses the MSPB (Multi-Sensor dataset with Phenotypic trait measurements from Bees) dataset. The data files are large (~200MB each) and not included in the Git repository. The project expects the following files in the `data/` directory:

- `D1_sensor_data.csv`: Sensor data from device 1
- `D1_ant.xlsx`: Annotations for device 1
- `D2_sensor_data.csv`: Sensor data from device 2
- `D2_ant.xlsx`: Annotations for device 2

Since the data files are too large for Git, you can:

1. **Option 1**: Download the files separately and place them in the `data/` directory
2. **Option 2**: Use Git LFS (Large File Storage) if you need to store them in your repository
3. **Option 3**: Store them in a GCS bucket and download them during setup

### Docker Issues

If you encounter Docker-related issues:
```bash
# Restart Docker daemon
docker system prune -a
docker-compose down
docker-compose up --build
```

### GCP Deployment Issues

If deployment to GCP fails:
```bash
# Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID

# Verify APIs are enabled
gcloud services list --enabled

# Check deployment logs
gcloud functions logs read beehive-processor
gcloud run services logs read beehive-dashboard
```

---

<p align="center">
  Made with ❤️ for 🐝
</p>

