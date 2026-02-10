Test task CRUD API on Django

- Included postman endpoints for testing
- No Docker or chache since I'm out of time :^)
- Views separated for clarity
- Verifications for duplicates/valid external ID/deletion of a project when a place is marked as visited

HOW TO RUN

1. Create virtual environment
python -m venv venv
venv\Scripts\activate     # Windows
# source venv/bin/activate  # macOS/Linux

2. Install dependencies
pip install -r requirements.txt

3. Run migrations
python manage.py makemigrations
python manage.py migrate

4. Start server
python manage.py runserver


API available at:

http://127.0.0.1:8000/api/
