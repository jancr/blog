
# core imports
import datetime
import pathlib
import os

# 3rd party imports
import peewee
from flask import Markup
from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.extra import ExtraExtension
from playhouse.flask_utils import FlaskDB
from playhouse.sqlite_ext import *
from micawber import bootstrap_basic, parse_html
from micawber.cache import Cache as OEmbedCache

db = FlaskDB()
oembed_providers = bootstrap_basic(OEmbedCache())


class Entry(db.Model):
    title = peewee.CharField()
    slug = peewee.CharField(unique=True)
    content = peewee.TextField()
    published = peewee.BooleanField(index=True)
    timestamp = peewee.DateTimeField(default=datetime.datetime.now, index=True)

    @property
    def html_content(self):
        """
        Generate HTML representation of the markdown-formatted blog entry,
        and also convert any media URLs into rich media objects such as video
        players or images.
        """
        hilite = CodeHiliteExtension(linenums=False, css_class='highlight')
        extras = ExtraExtension()
        markdown_content = markdown(self.content, extensions=[hilite, extras])
        oembed_content = parse_html(
            markdown_content,
            oembed_providers,
            urlize_all=True,
            #  maxwidth=app.config['SITE_WIDTH'])
            maxwidth=800) #  TODO get from blueprint
        return Markup(oembed_content)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = re.sub(r'[^\w]+', '-', self.title.lower()).strip('-')
        #  if kwargs.pop('load_from_disk', False):
        #      self.load_from_disk(kwargs.pop('markdown_path'), 
        #                          kwargs.pop('data_path'))
        #  elif kwargs.pop('to_disk', False):
        #      self.save_to_disk()

        ret = super(Entry, self).save(*args, **kwargs)
        self.update_search_index()
        return ret

    #  def save_to_disk(self):
    #      folder = pathlib.Path(APP_DIR) / "posts"
    #      folder.mkdir(exist_ok=True)
    #      (folder / f"{self.docid}.md").open('w').write(self.content)
    #      (folder / f"{self.slug}.data").open('w').write(
    #          f"Title: {self.title}\n"
    #          f"Slug: {self.slug}\n"
    #          f"Published: {self.published}\n"
    #          f"Time: {','.join(map(str, self.timestamp.timetuple[:7]))}\n")

    @classmethod
    def create_load_from_disk(cls, markdown_path, data_path):
        self = cls(title='', content='')
        self.docid = markdown_path.name.split('_', 1)[0]
        with open(data_path) as data_file:
            # TODO: make more dynamic (do not requre slug, and such)
            self.title = data_file.readline().rstrip('\n').split(' ')[-1]
            self.slug = data_file.readline().rstrip('\n').split(' ')[-1]
            self.published = bool(data_file.readline().rstrip('\n').split(' ')[-1])
            time_str = data_file.readline().rstrip('\n').split(' ')[-1]
            if time_str:
                self.time = datetime.datetime(*map(int, time_str.split(',')))
        if not time_str:
            time_str = ','.join(map(str, datetime.datetime.now().timetuple()[:7]))
            with open(data_path, 'a') as data_file:
                data_file.write(f"Time: {time_str}\n")
        with open(markdown_path) as markdown_file:
            self.content = markdown_file.read()
        return self

    def update_search_index(self):
        # Create a row in the FTSEntry table with the post content. This will
        # allow us to use SQLite's awesome full-text search extension to
        # search our entries.
        content = '\n'.join((self.title, self.content))
        if self.exists(self.docid):
            (FTSEntry
             .update({FTSEntry.content: content})
             .where(FTSEntry.docid == self.id)
             .execute())
        else:
            FTSEntry.insert({
                FTSEntry.docid: self.id,
                FTSEntry.content: content}).execute()

    @classmethod
    def exists(cls, docid):
        return (FTSEntry
                .select(FTSEntry.docid)
                .where(FTSEntry.docid == docid)
                .exists())


    @classmethod
    def public(cls):
        return Entry.select().where(Entry.published == True)

    @classmethod
    def drafts(cls):
        return Entry.select().where(Entry.published == False)

    @classmethod
    def search(cls, query):
        words = [word.strip() for word in query.split() if word.strip()]
        if not words:
            # Return an empty query.
            return Entry.noop()
        else:
            search = ' '.join(words)

        # Query the full-text search index for entries matching the given
        # search query, then join the actual Entry data on the matching
        # search result.
        return (Entry
                .select(Entry, FTSEntry.rank().alias('score'))
                .join(FTSEntry, on=(Entry.id == FTSEntry.docid))
                .where(
                    FTSEntry.match(search) &
                    (Entry.published == True))
                .order_by(SQL('score')))


class FTSEntry(FTSModel):
    content = peewee.TextField()

    class Meta:
        database = db.database


