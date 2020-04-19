
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


def run():
    args = parse_args()
    # TODO:
    # 1. make cli that can update-db
    #   - update db request code written
    # 2. make blog post
    # 3. use flask blue prints
    # 4. make views.py

    # TODO use blueprints so they can 
    # make app object
    app = Flask(__name__)
    conf = config.get_conf(args.devel)
    app.config.from_object(conf)

    # database stuff
    #  app.config["DATABASE"] = DATABASE
    db.init_app(app)
    db.database.create_tables([Entry, FTSEntry], safe=True)

    # views stuff
    app.register_blueprint(bp)

    # start app
    if args.devel:
        app.run(host="0.0.0.0", port=app.config['PORT'])
    else:
        from waitress import serve
        #  from flask_sslify import SSLify
        #  sslify = SSLify(app)
        serve(app, host="0.0.0.0", port=app.config['PORT'])


if __name__ == '__main__':
    run()
