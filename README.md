It is incredibly frustrating to be left waiting, but pivoting this into a portfolio piece is the exact right move. You built a secure, functioning full-stack integration with a major third-party API—that is prime material for a backend engineering resume.

To make it look like a standalone open-source project rather than an assignment, we will strip away the "VectorShift" specific terminology and focus on the architecture, security, and functionality. 

Here is a professional `README.md` you can copy directly into your repository.

***

# HubSpot CRM Integration Service

## 📖 Overview
A full-stack application demonstrating a secure, scalable integration with the HubSpot CRM API. This project implements a complete OAuth 2.0 authorization flow, securely handles token exchange and state validation, and maps raw third-party CRM data (Contacts) into a standardized internal data structure. 

This project is built to showcase robust backend architecture, API consumption, and secure credential handling.

## ✨ Key Features
* **Secure OAuth 2.0 Flow:** Full implementation of the HubSpot authorization code grant type, including secure callback handling and token extraction.
* **State Validation:** Utilizes Redis to temporarily store and validate the `state` parameter during the OAuth flow, protecting against Cross-Site Request Forgery (CSRF) attacks.
* **Data Transformation:** Queries the HubSpot V3 API (`crm.objects.contacts.read` scope) and standardizes the JSON response into strictly typed `IntegrationItem` objects.
* **Decoupled Architecture:** Clean separation of concerns between the React frontend (handling the popup authorization UI) and the FastAPI backend (handling secrets and API communication).

## 🛠️ Tech Stack
* **Backend:** Python, FastAPI, HTTPX (for async external API calls)
* **Frontend:** React, Material UI, Axios
* **Data & State:** Redis (for OAuth state validation)
* **External API:** HubSpot CRM V3 API

---

## 🚀 Getting Started

### Prerequisites
* Python 3.8+
* Node.js (v14+)
* Redis (Running locally or via Docker)
* A HubSpot Developer Account (to create a public app and get Client ID/Secret)

### 1. Environment Setup
You will need to create a `.env` file in the `backend` directory with your HubSpot application credentials:

```env
HUBSPOT_CLIENT_ID=your_client_id_here
HUBSPOT_CLIENT_SECRET=your_client_secret_here
HUBSPOT_REDIRECT_URI=http://localhost:8000/integrations/hubspot/oauth2callback
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 2. Backend Installation (FastAPI)
Open your terminal and navigate to the `backend` directory. 

```bash
cd backend

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
python -m uvicorn main:app --reload
```
*The backend will run on `http://localhost:8000`*

### 3. Frontend Installation (React)
Open a new, separate terminal and navigate to the `frontend` directory.

```bash
cd frontend

# Install Node modules
npm install

# Start the development server
npm start
```
*The frontend will run on `http://localhost:3000`*

## 💡 Usage Example
1.  Navigate to `http://localhost:3000` in your browser.
2.  Click **"Connect to HubSpot"** to initiate the OAuth popup window.
3.  Log in to your HubSpot account and grant the requested permissions.
4.  Once the button turns green indicating a successful connection, click **"Load Data"**.
5.  Check your backend terminal to view the successfully retrieved and mapped contact data.

## 🔒 Security Considerations
* **No Secrets in Browser:** The React frontend never sees the `client_secret` or the raw access tokens. All API calls to HubSpot are brokered through the FastAPI backend.
* **CSRF Protection:** The `state` parameter generated during the initial authorization request is cached in Redis with a short Time-To-Live (TTL) and rigorously verified upon the callback.
