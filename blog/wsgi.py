from app import run, get_app


app = get_app(devel=False)


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=app.config['PORT'])
