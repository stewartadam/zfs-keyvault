from flask_env import MetaFlaskEnv

class DefaultConfig(metaclass=MetaFlaskEnv):
    ENV_PREFIX = 'ZKV_'

    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///db.sqlite'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    AAD_RESOURCE = 'https://vault.azure.net'
    AAD_AUTHORITY_HOST_URI = 'https://login.microsoftonline.com'
    MAX_WAIT = 60
    PIN_LENGTH = 6

    AAD_CLIENT_ID = 'guid-here'
    AAD_CLIENT_SECRET = 'secret-here'
    AAD_TENANT_ID = 'guid-here'
    KEY_VAULT_URI = 'https://YOUR_KV_NAME.vault.azure.net'
    KEY_VAULT_SECRET = 'KV_SECRET_NAME'

    TWILIO_ACCOUNT_ID = 'id-here'
    TWILIO_TOKEN = 'token-here'
    SMS_TO = '+15551234567'
    SMS_FROM = '+15551234567'

class DevelopmentConfig(DefaultConfig):
    DEBUG = True
