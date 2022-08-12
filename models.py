from sqlalchemy import Column, String, Integer, Boolean, DateTime, ARRAY, ForeignKey
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()


def db_setup(app):
    app.config.from_object("config")
    db.app = app
    db.init_app(app)
    migrate = Migrate(app, db)
    return db


class Venue(db.Model):
    __tablename__ = "venues"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500), default="")
    facebook_link = db.Column(db.String(120), default="")

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
    website_link = db.Column(db.String(120), default="")
    looking_for_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500), default="")
    shows = db.relationship("Show", backref="venue", lazy=True)

    def __repr__(self):
        return f"<Venue {self.id} name: {self.name}>"


class Artist(db.Model):
    __tablename__ = "artists"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    genres = db.Column("genres", db.ARRAY(db.String()), nullable=False)
    image_link = db.Column(db.String(500), default="")
    facebook_link = db.Column(db.String(120), default="")

    # TODO: implement any missing fields, as a database migration using Flask-Migrate
    website_link = db.Column(db.String(120), default="")
    looking_for_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500), default="")

    shows = db.relationship("Show", backref="artist", lazy=True)

    def __repr__(self):
        return f"<Artist {self.id} name: {self.name}>"


# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.


class Show(db.Model):
    __tablename__ = "shows"

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey("venues.id"), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id"), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return f"<Show {self.id}, Artist {self.artist_id}, Venue {self.venue_id}>"
