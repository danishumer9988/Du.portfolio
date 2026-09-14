from pathlib import Path
import os

import dj_database_url
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from dotenv import load_dotenv


# ============================================================
# BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================================================
# ENVIRONMENT VARIABLES
# ============================================================

load_dotenv(BASE_DIR / ".env")


# ============================================================
# SECURITY
# ============================================================

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

if not SECRET_KEY:
    raise ValueError(
        "DJANGO_SECRET_KEY is not set. Add it to your .env file."
    )


DEBUG = os.getenv(
    "DJANGO_DEBUG",
    "True"
).lower() in {"1", "true", "yes"}


ALLOWED_HOSTS = ["*"]


# ============================================================
# APPLICATIONS
# ============================================================

INSTALLED_APPS = [
    # --- Unfold (must come before django.contrib.admin) ---
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    "unfold.contrib.import_export",

    # --- Django ---
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # --- Project ---
    "main",
]


# ============================================================
# MIDDLEWARE
# ============================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================================================
# URL CONFIGURATION
# ============================================================

ROOT_URLCONF = "portfolio.urls"


# ============================================================
# TEMPLATES
# ============================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "main.context_processors.admin_preferences",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "main.context_processors.site_context",
            ],
        },
    },
]


# ============================================================
# WSGI / ASGI
# ============================================================

WSGI_APPLICATION = "portfolio.wsgi.application"
ASGI_APPLICATION = "portfolio.asgi.application"


# ============================================================
# DATABASE
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


# ============================================================
# PASSWORD VALIDATION
# ============================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME":
        "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.MinimumLengthValidator"
    },
    {
        "NAME":
        "django.contrib.auth.password_validation.CommonPasswordValidator"
    },
]


# ============================================================
# INTERNATIONALIZATION
# ============================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Karachi"
USE_I18N = True
USE_TZ = True


# ============================================================
# MEDIA FILES
# ============================================================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ============================================================
# DEFAULT PRIMARY KEY
# ============================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================================
# SECURITY HEADERS
# ============================================================

SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
X_FRAME_OPTIONS = "DENY"


# ============================================================
# PRODUCTION SECURITY
# ============================================================

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True


# ============================================================
# EMAIL — Gmail SMTP
# ============================================================

EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "").strip()
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "").replace(" ", "").strip()

if EMAIL_HOST_USER and EMAIL_HOST_PASSWORD:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = True
    EMAIL_USE_SSL = False
    EMAIL_TIMEOUT = 20
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER or "danishumer9988@gmail.com",
)

CONTACT_RECEIVER_EMAIL = os.getenv(
    "CONTACT_RECEIVER_EMAIL",
    EMAIL_HOST_USER or "danishumer9988@gmail.com",
)


# ============================================================
# DJANGO UNFOLD — Admin theme
# ============================================================

UNFOLD = {
    "SITE_TITLE": "Portfolio Admin",
    "SITE_HEADER": "Danish Umer · CMS",
    "SITE_SUBHEADER": "Content management",
    "SITE_URL": "/",
    "SITE_SYMBOL": "dashboard",

    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": True,
    "SHOW_BACK_BUTTON": True,

    "THEME": None,
    "DARK_MODE_THRESHOLD": 0.6,
    "DARK_MODE_CLASS": "dark",
    "BORDER_RADIUS": "12px",

    "DASHBOARD_CALLBACK": "main.dashboard.dashboard_callback",

    "STYLES": [
        lambda request: "/static/css/admin-custom.css",
    ],

    "COLORS": {
        "primary": {
            "50":  "247 254 231", "100": "236 252 203", "200": "217 249 157",
            "300": "190 242 100", "400": "163 230 53",  "500": "132 204 22",
            "600": "101 163 13",  "700": "77 124 15",   "800": "63 98 18",
            "900": "54 83 20",    "950": "26 46 5",
        },
    },

    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": True,
        "navigation": [
            {
                "title": "Content",
                "separator": True,
                "items": [
                    {"title": "Projects", "icon": "folder_special",
                     "link": reverse_lazy("admin:main_project_changelist")},
                    {"title": "Services", "icon": "design_services",
                     "link": reverse_lazy("admin:main_service_changelist")},
                    {"title": "Experience", "icon": "work_history",
                     "link": reverse_lazy("admin:main_experience_changelist")},
                    {"title": "Reviews", "icon": "star",
                     "link": reverse_lazy("admin:main_review_changelist")},
                ],
            },
            {
                "title": "Taxonomy",
                "separator": True,
                "items": [
                    {"title": "Skills", "icon": "bolt",
                     "link": reverse_lazy("admin:main_skill_changelist")},
                    {"title": "Industries", "icon": "category",
                     "link": reverse_lazy("admin:main_industry_changelist")},
                ],
            },
            {
                "title": "Inbox",
                "separator": True,
                "items": [
                    {"title": "Contact messages", "icon": "mail",
                     "link": reverse_lazy("admin:main_contactmessage_changelist")},
                ],
            },
            {
                "title": "Site",
                "separator": True,
                "items": [
                    {"title": "Site settings", "icon": "settings",
                     "link": reverse_lazy("admin:main_sitesettings_changelist")},
                    {"title": "Social links", "icon": "share",
                     "link": reverse_lazy("admin:main_sociallink_changelist")},
                    {"title": "Admin preferences", "icon": "tune",
                     "link": reverse_lazy("admin:main_adminpreferences_changelist")},
                ],
            },
            {
                "title": "Access",
                "separator": True,
                "items": [
                    {"title": "Users", "icon": "people",
                     "link": reverse_lazy("admin:auth_user_changelist")},
                    {"title": "Groups", "icon": "group",
                     "link": reverse_lazy("admin:auth_group_changelist")},
                ],
            },
        ],
    },
}


# ============================================================
# STATIC FILES
# ============================================================

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

WHITENOISE_MAX_AGE = 31536000
WHITENOISE_USE_FINDERS = True