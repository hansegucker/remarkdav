from peewee import *

db = SqliteDatabase("sync.db")


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
