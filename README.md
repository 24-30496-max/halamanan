# H.A.L.A.M.A.N.A.N - Farmers Resource Exchange Platform

A Flask-based web application that connects farmers to share and exchange resources.

## Prerequisites

- Python 3.7+
- MySQL Server
- pip (Python package manager)

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd halamanan
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install flask flask-login werkzeug mysql-connector-python python-dotenv
   ```

4. **Set up environment variables:**
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` with your database credentials:
     ```
     FLASK_SECRET_KEY=your_secret_key_here
     DB_HOST=localhost
     DB_PORT=3306
     DB_USER=your_db_user
     DB_PASSWORD=your_db_password
     DB_NAME=halamanan07
     ```

5. **Create the database:**
   - Connect to MySQL and run the schema:
     ```bash
     mysql -u root -p < database_schema.sql
     ```

6. **Run the application:**
   ```bash
   python app.py
   ```

7. **Access the application:**
   - Open your browser and go to: `http://localhost:5000`

## Project Structure

```
halamanan/
├── app.py                      # Main Flask application
├── database_schema.sql         # Database schema
├── static/
│   └── style.css              # CSS styles
├── templates/                  # HTML templates
│   ├── base.html              # Base template
│   ├── home.html              # Home page
│   ├── login.html             # Login page
│   ├── register.html          # Registration page
│   ├── browse.html            # Browse resources
│   ├── profile.html           # User profile
│   ├── post_offer.html        # Post offers
│   ├── post_request.html      # Post requests
│   └── ... (other templates)
├── .env.example               # Environment variables template
└── README.md                  # This file
```

## Features

- User registration and authentication
- Browse and search resources
- Post offers and requests
- Resource connections and inquiries
- Payment management
- User profile management

## Security Notes

- Always use strong secret keys in production
- Store sensitive information in `.env` file (not in version control)
- Never commit `.env` file to the repository
- Change default database credentials before deployment

## Code Quality

This project follows Python best practices:
- Code is formatted with Black
- HTML templates have consistent indentation
- CSS is organized with clear sections
- SQL schema is properly documented

## License

[Add license information here]

## Contact

[Add contact information here]
