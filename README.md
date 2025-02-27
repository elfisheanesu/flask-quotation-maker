# Quotation Management System

A comprehensive web application for managing quotations, invoices, products, customers, and purchase orders.

## Features

- Customer Management
- Product Catalog
- Quotation Generation
- Invoice Creation
- Purchase Order Management
- User Authentication

## Requirements

- Python 3.8+
- Flask and its dependencies (see requirements.txt)
- wkhtmltopdf (for PDF generation)

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   ```
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
5. Run the application:
   ```
   python app.py
   ```
6. Access the application at `http://localhost:5000`

## PDF Generation
For PDF generation functionality to work, you need to install `wkhtmltopdf`:

1. Download wkhtmltopdf from: https://wkhtmltopdf.org/downloads.html
2. Install it on your system
3. Add the installation directory to your system's PATH environment variable

## Project Structure

- `app.py`: Main application file with routes and models
- `templates/`: HTML templates
  - `base.html`: Base template with navigation
  - `index.html`: Dashboard template
- `requirements.txt`: Project dependencies

## Database

The application uses SQLite as the database. The database file will be automatically created when you first run the application.
