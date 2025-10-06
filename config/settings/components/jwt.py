
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=51),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
}
