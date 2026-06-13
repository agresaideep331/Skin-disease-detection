# Skin Disease Detection Web Application

A complete full-stack AI web application for skin disease prediction using deep learning.

## Features

- **User Authentication**: Sign up and login with secure password hashing
- **Disease Prediction**: Upload skin images for AI-powered disease detection
- **Disease Information**: Comprehensive details about various skin diseases
- **Skin Care Tips**: Personalized skin care routines based on skin type
- **Prediction History**: Track all your predictions with confidence scores
- **User Profile**: View your personal information and prediction statistics

## System Requirements

- Python 3.8 or higher
- 4GB RAM minimum
- 500MB disk space

## Installation Guide

### Step 1: Install Python

Download Python from https://www.python.org/downloads/
- Windows: Use the installer and make sure to check "Add Python to PATH"
- macOS/Linux: Use your package manager or the official installer

Verify installation:
```bash
python --version
```

### Step 2: Create Virtual Environment

Navigate to the project folder and create a virtual environment:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

Install all required packages:
```bash
pip install -r requirements.txt
```

### Step 4: Place Model File

Copy your trained model file to the project root directory:
- File name: `skin_disease_model.h5`
- Location: Same folder as `app.py`

### Step 5: Run the Application

```bash
python app.py
```

The application will start on: `http://localhost:5000`

## Project Structure

```
├── app.py                 # Main Flask application
├── database.py           # Database operations
├── requirements.txt      # Python dependencies
├── skin_disease_model.h5 # Trained ML model
├── templates/            # HTML files
│   ├── login.html
│   ├── signup.html
│   ├── home.html
│   ├── predict.html
│   ├── about.html
│   ├── history.html
│   └── profile.html
├── static/
│   └── css/
│       └── style.css     # Styling
└── uploads/              # Temporary image uploads
```

## Usage

1. **Sign Up**: Create a new account with your details
2. **Login**: Use your credentials to access the app
3. **Home**: Learn about different skin types and care routines
4. **Predict**: Upload a skin image to get disease prediction
5. **About**: View detailed disease information
6. **History**: Check your previous predictions
7. **Profile**: View your account information

## Security

- Passwords are hashed using Werkzeug security
- User sessions are managed securely
- All pages require authentication
- Only allowed image formats (JPG, JPEG, PNG) are accepted

## Supported Diseases

The application can detect the following skin conditions:
- Acne and Rosacea
- Atopic Dermatitis
- Chickenpox
- Measles
- Melanoma Skin Cancer
- Psoriasis
- Tinea Ringworm and Fungal Infections
- Warts and Viral Infections
- Urticaria Hives
- And more...

## Troubleshooting

**Model file not found**: Ensure `skin_disease_model.h5` is in the project root directory

**Port already in use**: The app uses port 5000. If it's in use, modify the port in `app.py`:
```python
app.run(debug=True, port=5001)  # Change to any available port
```

**Permission denied**: Run terminal as administrator (Windows) or use `sudo` (macOS/Linux)

## Performance Notes

- First prediction may take longer as the model loads
- Image uploads limited to 16MB
- Recommended image size: 224x224 pixels or larger

## Browser Compatibility

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

This project is provided as-is for educational purposes.

## Support

For issues or questions, ensure:
1. Python 3.8+ is installed
2. All dependencies from requirements.txt are installed
3. Model file is in the correct location
4. Port 5000 is available
5. You're using a supported browser
