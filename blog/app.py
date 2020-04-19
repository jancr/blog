
# core imports
import argparse

# 3rd party imports
from flask import Flask
                   
# local imports
from views import bp
from models import Entry, FTSEntry, db
import config


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--devel', action='store_true', default=False)
    parser.add_argument('--production', action='store_true', default=False)

    args = parser.parse_args()
    if args.devel + args.production != 1:
        raise ValueError("set ONE of --devel and --production")
    return args


def get_app(devel=True):
    # make app object
    app = Flask(__name__)
    conf = config.get_conf(devel)
    app.config.from_object(conf)

    # database stuff
    db.init_app(app)
    db.database.create_tables([Entry, FTSEntry], safe=True)

    # views stuff
    app.register_blueprint(bp)
    return app


def run(devel=True):
    app = get_app(devel)
    if devel:
        app.run(host="0.0.0.0", port=app.config['PORT'])
    else:
        from waitress import serve
        serve(app, host="0.0.0.0", port=app.config['PORT'])


if __name__ == '__main__':
    args = parse_args()
    run(args.devel)
