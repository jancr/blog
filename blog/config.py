
# core imports
import pathlib

# local imports
import secret

app_dir = pathlib.Path(__file__).parent.resolve()

class BaseConfig:
    DOMAIN = 'https://blog.badprior.com'  # TODO don't hardcode??
    APP_DIR = app_dir
    SECRET_KEY = secret.SECRET_KEY
    SITE_WIDTH = 800
    STATIC_DIR = app_dir / 'static'
    SECRET_DB_URL = secret.SECRET_DB_URL
    PORT = 5001
    HOST_NAME = '0.0.0.0'

    @property
    def POSTS_MARKDOWN_DIR(cls):
        return cls.POSTS_DIR / 'markdown'

    @property
    def POSTS_META_DIR(cls):
        return cls.POSTS_DIR / 'meta'

    @property
    def POSTS_STATIC_DIR(cls):
        return cls.POSTS_DIR / 'static'

    @property
    def BASE_URL(cls):
        return f'{cls.WEB_PROTOCOL}://{cls.HOST_NAME}:{cls.PORT}'


class ProductionConfig(BaseConfig):
    POSTS_DIR = BaseConfig.STATIC_DIR / 'posts'
    DEBUG = False
    DEVELOPMENT = False
    DATABASE = f'sqliteext:///{BaseConfig.APP_DIR / "blog.db"}'
    PORT = 443
    #  PORT = 80
    WEB_PROTOCOL = 'https'
    HOST_NAME = 'badprior.com'


class DevelopmentConfig(BaseConfig):
    #  POSTS_DIR = BaseConfig.STATIC_DIR / 'test_posts'
    POSTS_DIR = BaseConfig.STATIC_DIR / 'posts'
    DEBUG = True
    DEVELOPMENT = True
    DATABASE = f'sqliteext:///{BaseConfig.APP_DIR / "devel.db"}'
    #  PORT = 5000
    WEB_PROTOCOL = 'http'


def get_conf(devel=True):
    if devel:
        return DevelopmentConfig()
    return ProductionConfig()
