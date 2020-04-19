
# core imports
import pathlib

# local imports
import secret

app_dir = pathlib.Path(__file__).parent.resolve()

class BaseConfig:
    APP_DIR = app_dir
    SECRET_KEY = secret.SECRET_KEY
    SITE_WIDTH = 800
    STATIC_DIR = app_dir / 'static'
    SECRET_DB_URL = secret.SECRET_DB_URL
    PORT = 5001

    @property
    def POSTS_MARKDOWN_DIR(cls):
        return cls.POSTS_DIR / 'markdown'

    @property
    def POSTS_META_DIR(cls):
        return cls.POSTS_DIR / 'meta'


class ProductionConfig(BaseConfig):
    POSTS_DIR = BaseConfig.STATIC_DIR / 'posts'
    DEBUG = False
    DEVELOPMENT = False
    DATABASE = f'sqliteext:///{BaseConfig.APP_DIR / "blog.db"}'
    #  PORT = 443
    #  PORT = 80
    #  WEB_PROTOCOL = 'https'
    WEB_PROTOCOL = 'http'


class DevelopmentConfig(BaseConfig):
    POSTS_DIR = BaseConfig.STATIC_DIR / 'test_posts'
    DEBUG = True
    DEVELOPMENT = True
    DATABASE = f'sqliteext:///{BaseConfig.APP_DIR / "devel.db"}'
    #  PORT = 5000
    WEB_PROTOCOL = 'http'


def get_conf(devel=True):
    if devel:
        return DevelopmentConfig()
    return ProductionConfig()
