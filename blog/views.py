
# core imports
import urllib
import re
import datetime
import pathlib

# 3rd party imports
import flask
from flask import current_app as app
from flask import render_template, request, Response
from playhouse.flask_utils import get_object_or_404, object_list

# local imports
import secret
from models import Entry, FTSEntry, db, MetaFileError, Series
import rss


bp = flask.Blueprint('bp', __name__)


#  def parse_markdown(markdown_path):
#      with open(markdown_path) as markdown_file:
#          title = markdown_file.readline().lstrip('# ').rstrip(' \r\n')
#          # TODO: only in math context
#          content = markdown_file.read().lstrip(' \r\n')
#          content = re.sub(r'\\\\', r'\\newline', content)
#      return title, content
#  
#  
#  def update_entry(entry, markdown_path, data_path):
#      entry.docid = markdown_path.name.split('_', 1)[0]
#      entry.title, entry.content = parse_markdown(markdown_path)
#      #  with open(markdown_path) as markdown_file:
#      #      entry.title = markdown_file.readline().lstrip('# ').rstrip(' \r\n')
#      #      entry.content = markdown_file.read().lstrip(' \r\n')
#      with open(data_path) as data_file:
#          # TODO: make more dynamic (do not requre slug, and such)
#          #  entry.title = data_file.readline().rstrip('\n').split(': ')[-1]
#          entry.slug = data_file.readline().rstrip('\n').split(': ')[-1]
#          entry.published = bool(data_file.readline().rstrip('\n').split(' ')[-1])
#          time_str = data_file.readline().rstrip('\n').split(': ')[-1]
#          if time_str:
#              entry.time = datetime.datetime(*map(int, time_str.split(',')))
#      if not time_str:
#          time_str = ','.join(map(str, datetime.datetime.now().timetuple()[:7]))
#          with open(data_path, 'a') as data_file:
#              data_file.write(f"Time: {time_str}\n")


@bp.route(f'/db/{secret.SECRET_DB_URL}/<docid>')
def post_blog(docid):
    markdown_file = data_file = None
    try:
        markdown_file = next(app.config["POSTS_MARKDOWN_DIR"].glob(f"{docid}_*.md"))
        data_file = next(app.config["POSTS_META_DIR"].glob(f"{docid}_*.meta"))
    except StopIteration:
        error = ""
        if markdown_file is None:
            error += ' - the markdown file does not exist\n'
        if data_file is None:
            error += ' - the data file does not exist\n'
        return error
    try:
        entry = Entry.create_or_update_from_disk(markdown_file, data_file)
    except MetaFileError as e:
        return str(e)
    #  update_entry(entry, markdown_file, data_file)
    with db.database.atomic():
        entry.save()
    return f"{docid} Success!"


@bp.route('/')
def index():
    search_query = request.args.get('q')
    if search_query:
        query = Entry.search(search_query)
    else:
        query = Entry.public().order_by(Entry.timestamp.desc())

    # The `object_list` helper will take a base query and then handle
    # paginating the results if there are more than 20. For more info see
    # the docs:
    # http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#object_list
    return object_list('index.html', query, search=search_query, check_bounds=False)


def send_data(folder, filename):
    filename = str(app.config["POSTS_STATIC_DIR"] / folder / filename)
    return flask.send_file(filename)


@bp.route('/blog_id/<slug>/',  defaults={'folder': None, 'filename': None})
@bp.route('/blog_id/<docid>/')
def document(docid, folder, filename):
    if folder is not None:
        return send_data(folder, filename)
    entry = get_object_or_404(Entry.public(), Entry.id == docid)
    return render_template('detail.html', entry=entry)


@bp.route('/blog/<slug>/',  defaults={'folder': None, 'filename': None})
@bp.route('/blog/<slug>/<folder>/<filename>')
def detail(slug, folder, filename):
    if folder is not None:
        return send_data(folder, filename)
    query = Entry.public()
    entry = get_object_or_404(query, Entry.slug == slug)
    return render_template('detail.html', entry=entry, series=Series(entry))


def get_feed_generator(feed_url):
    domain = pathlib.Path(app.config["DOMAIN"])
    fg = rss.get_feed(str(domain / feed_url))
    for entry in Entry.public().order_by(Entry.timestamp.desc()):
        rss.add_entry(fg, entry, domain)
    return fg


@bp.route('/feed/rss')
def rss_feed():
    feed = get_feed_generator('feed/rss').rss_str()
    return Response(feed, mimetype='application/rss+xml')
    #  response = make_response(fg.rss_str())
    #  response.headers.set('Content-Type', 'application/rss+xml')


#  @bp.route('/feed/atom')
#  def atom_feed():
#      return get_feed_generator().atom_str()
#  

@bp.errorhandler(404)
def not_found(exc):
    return Response('<h3>Not found</h3>'), 404


@bp.app_template_filter('clean_querystring')
def clean_querystring(request_args, *keys_to_remove, **new_values):
    # We'll use this template filter in the pagination include. This filter
    # will take the current URL and allow us to preserve the arguments in the
    # querystring while replacing any that we need to overwrite. For instance
    # if your URL is /?q=search+query&page=2 and we want to preserve the search
    # term but make a link to page 3, this filter will allow us to do that.
    querystring = dict((key, value) for key, value in request_args.items())
    for key in keys_to_remove:
        querystring.pop(key, None)
    querystring.update(new_values)
    return urllib.urlencode(querystring)


# This hook ensures that a connection is opened to handle any queries
# generated by the request.
#  @bp.before_request
#  def _db_connect():
#      db.database.connect()

# This hook ensures that the connection is closed when we've finished
# processing the request.
#  @bp.teardown_request
#  def _db_close(exc):
#      if not db.database.is_closed():
#          db.database.close()
