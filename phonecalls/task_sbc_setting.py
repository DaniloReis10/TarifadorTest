# SeuProjeto/settings.py
from pathlib import Path
import os

# --- Caminhos básicos ---
BASE_DIR = Path(__file__).resolve().parent.parent  # raiz do projeto
APP_DIR = BASE_DIR  # onde estão os apps (ex.: phonecalls/, voip/, core/)

# --- Segurança / Debug ---
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-unsafe-secret")
DEBUG = os.getenv("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# --- Aplicativos instalados ---
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Seus apps do projeto (ajuste nomes conforme seus pacotes)
    "core",
    "phonecalls",
    "voip",
]

# --- Middlewares básicos ---
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# --- URLs / WSGI (ajuste o nome do módulo do projeto se quiser) ---
ROOT_URLCONF = "SeuProjeto.urls"          # crie um urls.py simples se for usar admin
WSGI_APPLICATION = "SeuProjeto.wsgi.application"

# --- Templates (necessário para admin; minimalista) ---
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Banco de Dados ---
# PROD (PostgreSQL) — defina via variáveis de ambiente
if os.getenv("DB_ENGINE", "sqlite") == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "tarifador"),
            "USER": os.getenv("POSTGRES_USER", "tarifador"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "senha"),
            "HOST": os.getenv("POSTGRES_HOST", "127.0.0.1"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }
else:
    # DEV (SQLite) — prático para rodar scripts como o task_sbc.py
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --- Idioma e timezone ---
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Fortaleza"
USE_I18N = True
USE_TZ = True  # mantenha True; Django salva em UTC e converte para TIME_ZONE

# --- Arquivos estáticos (para admin) ---
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- AutoField padrão ---
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Celery (ajuste se for usar broker/resultado) ---
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")
# Se não usar Redis, pode apontar para RabbitMQ, ou simplesmente deixar sem uso ao rodar task localmente.

# --- Log minimalista (útil p/ depurar o pipeline) ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}

# --- Config específico seu (opcional) ---
# Se futuramente quiser ler números controlados via settings/env em vez de DB:
# SBC_CONTROLLED_NUMBERS = os.getenv("SBC_CONTROLLED_NUMBERS", "").split(",")
