# Danish Umer — Premium Django Portfolio

A production-oriented personal developer portfolio + lightweight CMS built with:
- Python
- Django
- SQLite
- Django Templates
- HTML5 / CSS3
- Vanilla JavaScript
- Pillow for uploaded images

Exactly one Django app is used: `main`.

## Run

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py seed_demo
python manage.py runserver
```

Open:
- Public site: http://127.0.0.1:8000/
- Admin: http://127.0.0.1:8000/admin/

## Content management

The public site has no visitor account system. Django Admin is the only authentication surface.

Manage:
Projects, Project Images, Skills, Services, Industries, Experience, Reviews, Contact Messages, Social Links, Site Settings.

## Notes

- `MEDIA_ROOT` is `media/`.
- Static assets are intentionally consolidated into template files for the page-specific UI, with only a tiny global `static/admin-extra.css` placeholder available for future admin work.
- A PostgreSQL-ready architecture is used: standard Django ORM, relational fields, indexes, validators, and no SQLite-specific SQL.
