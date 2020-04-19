
# core imports
import urllib

# 3rd party imports
from flask import Blueprint
from flask import current_app as app
from flask import render_template, request, Response
from playhouse.flask_utils import get_object_or_404, object_list

# local imports
import secret
from models import Entry, FTSEntry, db


bp = Blueprint('bp', __name__)


def update_entry(entry, markdown_path, data_path):
    import datetime
    entry.docid = markdown_path.name.split('_', 1)[0]
    with open(data_path) as data_file:
        # TODO: make more dynamic (do not requre slug, and such)
        entry.title = data_file.readline().rstrip('\n').split(' ')[-1]
        entry.slug = data_file.readline().rstrip('\n').split(' ')[-1]
        entry.published = bool(data_file.readline().rstrip('\n').split(' ')[-1])
        time_str = data_file.readline().rstrip('\n').split(' ')[-1]
        if time_str:
            entry.time = datetime.datetime(*map(int, time_str.split(',')))
    if not time_str:
        time_str = ','.join(map(str, datetime.datetime.now().timetuple()[:7]))
        with open(data_path, 'a') as data_file:
            data_file.write(f"Time: {time_str}\n")
    with open(markdown_path) as markdown_file:
        entry.content = markdown_file.read()


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

    if Entry.exists(docid):
        entry = FTSEntry.get(FTSEntry.docid == docid)
    else:
        entry = Entry(title='', content='', docid=docid)

    update_entry(entry, markdown_file, data_file)
    with db.database.atomic():
        entry.save()
    return f"{docid} Success!"


@bp.route('/blog_id/<docid>/')
def document(docid):
    entry = get_object_or_404(Entry.public(), Entry.id == docid)
    return render_template('detail.html', entry=entry)


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


@bp.route('/blog/<slug>/')
def detail(slug):
    #  if session.get('logged_in'):
    #      query = Entry.select()
    #  else:
    query = Entry.public()
    entry = get_object_or_404(query, Entry.slug == slug)
    return render_template('detail.html', entry=entry)


@bp.errorhandler(404)
def not_found(exc):
    return Response('<h3>Not found</h3>'), 404


#  TODO: figure out how this works with bps!
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
