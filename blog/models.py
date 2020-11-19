
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


class MetaFileError(Exception):
    pass


class Series:
    def __init__(self, entry):
        self.entry = entry
        self._series = entry.get_series(entry.series)
        if entry.series:
            self.series = {s.part: s for s in self._series}
            self.parts = {s.part for s in self._series}
            #  self.slugs = {s.part: s.slug for s in self.series}

    @property 
    def first(self):
        return self.series[min(self.parts)]

    #  @property
    #  def firts_slug(self):
    #      return self.slugs[self.first]

    @property
    def last(self):
        return self.series[max(self.parts)]

    #  @property
    #  def last_slug(self):
    #      return self.slugs[self.last]

    @property
    def next(self):
        if self.entry.part + 1 in self.parts:
            return self.series[self.entry.part + 1]
        return None

    #  @property
    #  def next_slug(self):
    #      if self.next is not None:
    #          return self.slugs[self.next]

    @property
    def previous(self):
        if self.entry.part - 1 in self.parts:
            return self.series[self.entry.part - 1]
        return None

    #  @property
    #  def previous_slug(self):
    #      if self.previous is not None:
    #          return self.slugs[self.previous]
        

class Entry(db.Model):
    title = peewee.CharField()
    slug = peewee.CharField(unique=True)
    content = peewee.TextField()
    published = peewee.BooleanField(index=True)
    series = peewee.CharField(index=True, null=True)
    part = peewee.IntegerField(null=True)
    timestamp = peewee.DateTimeField(default=datetime.datetime.now, index=True)
    github_file = peewee.CharField(unique=True)

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
        #  if not self.slug:
        if self.series and self.part:
            base_slug = re.sub(r'[^\w]+', '-', self.series.lower()).strip('-')
            self.slug = f"{base_slug}-{self.part}"
        else:
            self.slug = re.sub(r'[^\w]+', '-', self.title.lower()).strip('-')
        #  if kwargs.pop('load_from_disk', False):
        #      self.load_from_disk(kwargs.pop('markdown_path'), 
        #                          kwargs.pop('data_path'))
        #  elif kwargs.pop('to_disk', False):
        #      self.save_to_disk()

        ret = super(Entry, self).save(*args, **kwargs)
        self.update_search_index()
        return ret

    @classmethod
    def _parse_markdown(cls, markdown_path):
        with open(markdown_path) as markdown_file:
            title = markdown_file.readline().lstrip('# ').rstrip(' \r\n')
            # TODO: only in math context
            content = markdown_file.read().lstrip(' \r\n')
            content = re.sub(r'\\\\', r'\\newline', content)
        return title, content

    @classmethod
    def create_or_update_from_disk(cls, markdown_path, data_path):
        docid = markdown_path.name.split('_', 1)[0]
        if cls.exists(docid):
            self = cls.get(cls.id == docid)
        else:
            self = cls(title='', content='', docid=docid)

        self.docid = markdown_path.name.split('_', 1)[0]
        self.title, self.content = cls._parse_markdown(markdown_path)
        self.github_file = markdown_path.resolve().name  # get file name, not link name
        with open(data_path) as data_file:
            for line in data_file:
                attr, value = line.rstrip('\n').split(': ')
                attr = attr.lower()
                if not hasattr(self.__class__, attr):
                    raise MetaFileError(f"{attr} is not a valid field of {self.__class__}")
                if attr == 'published':
                    value = bool(value)
                elif attr == 'timestamp':
                    value = datetime.datetime(*map(int, value.split(',')))
                setattr(self, attr, value)
            #  self.slug = data_file.readline().rstrip('\n').split(': ')[-1]
            #  self.published = bool(data_file.readline().rstrip('\n').split(' ')[-1])
            #  time_str = data_file.readline().rstrip('\n').split(': ')[-1]
            #  if time_str:
            #      self.time = datetime.datetime(*map(int, time_str.split(',')))
        if not hasattr(self, 'timestamp'):
            time_str = ','.join(map(str, datetime.datetime.now().timetuple()[:7]))
            with open(data_path, 'a') as data_file:
                data_file.write(f"Timestamp: {time_str}\n")
            self.time = datetime.datetime(*map(int, time_str.split(',')))
        #  if not hasattr(self, 'series') or not hasattr(self, 'part'):
        #      self.series = 'None'
        #      self.part = -1
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
    def get_series(cls, series):
        return cls.select().where(cls.series == series)

    @classmethod
    def public(cls):
        return cls.select().where(cls.published == True)

    @classmethod
    def drafts(cls):
        return cls.select().where(cls.published == False)

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

    class Meta:
        database = db.database


class FTSEntry(FTSModel):
    content = peewee.TextField()

    class Meta:
        database = db.database



