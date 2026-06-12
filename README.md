# ClassiFind AI – Legal Classified Document Analysis Platform

An AI-powered platform for processing, extracting, and searching classified advertisements from authorized documents.

## Features

✅ **Document Upload System** – User/admin PDF and image uploads  
✅ **OCR Processing** – Convert documents to searchable text  
✅ **AI Extraction** – Automatic classified ad extraction  
✅ **Smart Search** – Find classifieds by keyword, category, location, date  
✅ **Dashboard** – Real-time analytics and statistics  
✅ **Legal Compliance** – Only processes authorized documents  

## Tech Stack

- **Backend**: Django 4.2 + Django REST Framework
- **Database**: SQLite
- **OCR**: Tesseract + EasyOCR
- **NLP**: spaCy
- **Frontend**: HTML/CSS/JavaScript

## Project Structure

```
classifind-ai/
├── manage.py
├── requirements.txt
├── db.sqlite3
├── classifind/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── classified_app/
│   ├── models.py           # Database models
│   ├── views.py            # API views
│   ├── ocr_engine.py       # OCR processing
│   ├── nlp_engine.py       # AI extraction
│   ├── forms.py
│   ├── serializers.py
│   └── urls.py
├── media/uploads/          # Uploaded PDFs/images
├── logs/                    # Processing logs
└── templates/
    └── dashboard.html
```

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Initialize database: `python manage.py migrate`
4. Create superuser: `python manage.py createsuperuser`
5. Run server: `python manage.py runserver`

## Database

- **Type**: SQLite
- **Location**: `db.sqlite3`
- **Tables**: DocumentUpload, ExtractedClassified, Category, Location, SearchLog

## API Endpoints

- `POST /api/upload/` – Upload classified document
- `GET /api/classifieds/` – List all classifieds
- `GET /api/search/?q=keyword` – Search classifieds
- `GET /api/dashboard/stats/` – Get statistics
- `GET /api/classifieds/by-category/` – Filter by category
- `GET /api/classifieds/by-location/` – Filter by location

## Usage

See full documentation in SETUP.md

## License

MIT License - See LICENSE file
