from peewee import BooleanField, CharField, DateTimeField, Model, SqliteDatabase

from remarkdav.config import settings

db = SqliteDatabase(settings.get("db_path", "sync.db"))


class File(Model):
    path = CharField()
    source = CharField()
    modified = DateTimeField(null=True)
    downloaded = BooleanField(default=False)
    uploaded = BooleanField(default=False)
    upload_path = CharField(default="", null=True)
    local_path = CharField(default="", null=True)

    class Meta:
        database = db


db.create_tables([File], safe=True)
