# Gratitude Journal Project

## Introduction
A web application designed to allow users to track their gratitude entries, analyze sentiment, and view statistics.

## Features
- User authentication
- Adding, modifying, and deleting journal entries
- Sentiment analysis with Azure Cognitive Services
- Admin capabilities for managing all entries
- Responsive and interactive UI

## Technologies Used
- **Backend**: Flask, Flask-Login
- **Frontend**: HTML, CSS, JavaScript
- **Services**: Azure Text Analytics, Azure Storage Tables
- **Database**: Azure Storage Tables

## Setup Instructions
1. **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/Journal_Gratitude.git
    cd Journal_Gratitude
    ```

2. **Create a virtual environment**:
    ```bash
    python -m venv env
    env\Scripts\activate  # Windows
    source env/bin/activate  # macOS/Linux
    ```

3. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables**:
    Update the `config.py` file with your Azure Text Analytics and Storage Table credentials:
    ```python
    TEXT_ANALYTICS_ENDPOINT = "your-text-analytics-endpoint"
    TEXT_ANALYTICS_KEY = "your-text-analytics-key"
    STORAGE_CONNECTION_STRING = "your-storage-connection-string"
    TABLE_NAME = "GratitudeEntries"
    ```

5. **Run the application**:
    ```bash
    python app.py
    ```

## Deployment
- Deploy using Docker or Azure App Services:
    - **Docker**:
        ```bash
        docker build -t flask-gratitude-app .
        docker tag flask-gratitude-app yourdockerhubusername/flask-gratitude-app:latest
        docker push yourdockerhubusername/flask-gratitude-app:latest
        ```
    - **Azure CLI**:
        ```bash
        az webapp deploy --resource-group GratitudeAppRG --name gratitude-journal-app --src-path app.zip --type zip
        ```

## License
MIT License
