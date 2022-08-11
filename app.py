# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

from email.policy import default
import json
from operator import or_
import sys
from time import sleep

# from tkinter import ttk
from unicodedata import name
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import desc
from forms import *
from flask_migrate import Migrate
import config

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


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


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():

    artists_raw = (
        Artist.query.with_entities(Artist.id, Artist.name)
        .order_by(desc(Artist.id))
        .limit(10)
        .all()
    )
    venues_raw = (
        Venue.query.with_entities(Venue.id, Venue.name)
        .order_by(desc(Venue.id))
        .limit(10)
        .all()
    )
    artists, venues = [], []
    for artist in artists_raw:
        artists.append({"id": artist.id, "name": artist.name})
    for venue in venues_raw:
        venues.append({"id": venue.id, "name": venue.name})
    return render_template("pages/home.html", artists=artists, venues=venues)


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    # TODO: replace with real venues data.
    locations = (
        Venue.query.with_entities(Venue.city, Venue.state).distinct(Venue.state).all()
    )

    res = []
    for location in locations:
        city, state = location

        venues = Venue.query.filter(Venue.city == city, Venue.state == state).all()

        res_venues = []
        for venue in venues:
            res_venues.append(
                {
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": len(futureShowsCheck(venue.shows)),
                }
            )

        res.append({"city": city, "state": state, "venues": res_venues})
    #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
    # data = [
    #     {
    #         "city": "San Francisco",
    #         "state": "CA",
    #         "venues": [
    #             {
    #                 "id": 1,
    #                 "name": "The Musical Hop",
    #                 "num_upcoming_shows": 0,
    #             },
    #             {
    #                 "id": 3,
    #                 "name": "Park Square Live Music & Coffee",
    #                 "num_upcoming_shows": 1,
    #             },
    #         ],
    #     },
    #     {
    #         "city": "New York",
    #         "state": "NY",
    #         "venues": [
    #             {
    #                 "id": 2,
    #                 "name": "The Dueling Pianos Bar",
    #                 "num_upcoming_shows": 0,
    #             }
    #         ],
    #     },
    # ]
    return render_template("pages/venues.html", areas=res)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    search_word = request.form["search_term"]
    result = Venue.query.filter(
        or_(
            Venue.name.ilike(f"%{search_word}%"),
            Venue.city.concat(", ").concat(Venue.state).like(f"{search_word}%"),
        )
    ).all()

    response = {
        "count": len(result),
        "data": [
            {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": len(futureShowsCheck(venue.shows)),
            }
            for venue in result
        ],
    }
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    # response = {
    #     "count": 1,
    #     "data": [
    #         {
    #             "id": 2,
    #             "name": "The Dueling Pianos Bar",
    #             "num_upcoming_shows": 0,
    #         }
    #     ],
    # }
    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    current_venue = Venue.query.get(venue_id)
    past_shows = []
    upcoming_shows = []
    current_time = datetime.now()

    for show in current_venue.shows:
        artist = (
            db.session.query(Artist.id, Artist.name, Artist.image_link)
            .filter_by(id=show.artist_id)
            .first()
        )

        artist_data = {
            "artist_id": artist.id,
            "artist_name": artist.name,
            "artist_image_link": artist.image_link,
            "start_time": str(show.start_time),
        }

        if show.start_time > current_time:
            upcoming_shows.append(artist_data)
        else:
            past_shows.append(artist_data)

    data = {
        "id": current_venue.id,
        "name": current_venue.name,
        # "genres": current_venue.genres.replace("{", "").replace("}", "").split(","),
        "genres": current_venue.genres,
        "address": current_venue.address,
        "city": current_venue.city,
        "state": current_venue.state,
        "phone": current_venue.phone,
        "website": current_venue.website_link,
        "facebook_link": current_venue.facebook_link,
        "seeking_talent": current_venue.looking_for_talent,
        "seeking_description": current_venue.seeking_description,
        "image_link": current_venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }

    # data1 = {
    #     "id": 1,
    #     "name": "The Musical Hop",
    #     "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    #     "address": "1015 Folsom Street",
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "123-123-1234",
    #     "website": "https://www.themusicalhop.com",
    #     "facebook_link": "https://www.facebook.com/TheMusicalHop",
    #     "seeking_talent": True,
    #     "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    #     "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
    #     "past_shows": [
    #         {
    #             "artist_id": 4,
    #             "artist_name": "Guns N Petals",
    #             "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    #             "start_time": "2019-05-21T21:30:00.000Z",
    #         }
    #     ],
    #     "upcoming_shows": [],
    #     "past_shows_count": 1,
    #     "upcoming_shows_count": 0,
    # }
    # data2 = {
    #     "id": 2,
    #     "name": "The Dueling Pianos Bar",
    #     "genres": ["Classical", "R&B", "Hip-Hop"],
    #     "address": "335 Delancey Street",
    #     "city": "New York",
    #     "state": "NY",
    #     "phone": "914-003-1132",
    #     "website": "https://www.theduelingpianos.com",
    #     "facebook_link": "https://www.facebook.com/theduelingpianos",
    #     "seeking_talent": False,
    #     "image_link": "https://images.unsplash.com/photo-1497032205916-ac775f0649ae?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=750&q=80",
    #     "past_shows": [],
    #     "upcoming_shows": [],
    #     "past_shows_count": 0,
    #     "upcoming_shows_count": 0,
    # }
    # data3 = {
    #     "id": 3,
    #     "name": "Park Square Live Music & Coffee",
    #     "genres": ["Rock n Roll", "Jazz", "Classical", "Folk"],
    #     "address": "34 Whiskey Moore Ave",
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "415-000-1234",
    #     "website": "https://www.parksquarelivemusicandcoffee.com",
    #     "facebook_link": "https://www.facebook.com/ParkSquareLiveMusicAndCoffee",
    #     "seeking_talent": False,
    #     "image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #     "past_shows": [
    #         {
    #             "artist_id": 5,
    #             "artist_name": "Matt Quevedo",
    #             "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    #             "start_time": "2019-06-15T23:00:00.000Z",
    #         }
    #     ],
    #     "upcoming_shows": [
    #         {
    #             "artist_id": 6,
    #             "artist_name": "The Wild Sax Band",
    #             "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #             "start_time": "2035-04-01T20:00:00.000Z",
    #         },
    #         {
    #             "artist_id": 6,
    #             "artist_name": "The Wild Sax Band",
    #             "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #             "start_time": "2035-04-08T20:00:00.000Z",
    #         },
    #         {
    #             "artist_id": 6,
    #             "artist_name": "The Wild Sax Band",
    #             "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #             "start_time": "2035-04-15T20:00:00.000Z",
    #         },
    #     ],
    #     "past_shows_count": 1,
    #     "upcoming_shows_count": 1,
    # }
    # data = list(filter(lambda d: d["id"] == venue_id, [data1, data2, data3]))[0]
    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        form = VenueForm(request.form)
        create_new_venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            image_link=form.image_link.data,
            genres=form.genres.data,
            facebook_link=form.facebook_link.data,
            seeking_description=form.seeking_description.data,
            looking_for_talent=form.seeking_talent.data,
            website_link=form.website_link.data,
        )

        db.session.add(create_new_venue)
        db.session.commit()
        # on successful db insert, flash success
        flash("Venue " + request.form["name"] + " was successfully listed!")
    # TODO: on unsuccessful db insert, flash an error instead.
    except:
        db.session.rollback()
        flash(
            "An error occurred. Venue" + request.form["name"] + " could not be listed"
        )
        print(sys.exc_info())
    finally:
        db.session.close()
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template("pages/home.html")


@app.route("/venues/<venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    venue = Venue.query.get(venue_id)
    name = venue.name
    try:
        db.session.delete(venue)
        db.session.commit()
        flash("Venue " + name + " was successflly deleted")
    except:
        # print(e)
        db.session.rollback()
        flash("Venue " + name + " couldn't be deleted.")
        print(sys.exc_info())
    finally:
        db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return redirect(url_for("index"))


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    # TODO: replace with real data returned from querying the database
    data = []
    artists = Artist.query.with_entities(Artist.id, Artist.name).all()

    for artist in artists:
        data.append({"id": artist.id, "name": artist.name})

    # data = [
    #     {
    #         "id": 4,
    #         "name": "Guns N Petals",
    #     },
    #     {
    #         "id": 5,
    #         "name": "Matt Quevedo",
    #     },
    #     {
    #         "id": 6,
    #         "name": "The Wild Sax Band",
    #     },
    # ]
    return render_template("pages/artists.html", artists=data)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_word = request.form["search_term"]
    result = Artist.query.filter(
        or_(
            Artist.name.ilike(f"%{search_word}%"),
            Artist.city.concat(", ").concat(Artist.state).like(f"{search_word}%"),
        )
    ).all()

    response = {
        "count": len(result),
        "data": [
            {
                "id": artist.id,
                "name": artist.name,
                "num_upcoming_shows": len(futureShowsCheck(artist.shows)),
            }
            for artist in result
        ],
    }

    # response = {
    #     "count": 1,
    #     "data": [
    #         {
    #             "id": 4,
    #             "name": "Guns N Petals",
    #             "num_upcoming_shows": 0,
    #         }
    #     ],
    # }
    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=request.form.get("search_term", ""),
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using artist_id
    current_artist = Artist.query.get(artist_id)
    shows = Show.query.filter_by(artist_id=artist_id).all()
    past_shows = []
    upcoming_shows = []
    current_time = datetime.now()

    for show in shows:
        artist_data = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": str(show.start_time),
        }

        if show.start_time > current_time:
            upcoming_shows.append(artist_data)
        else:
            past_shows.append(artist_data)

    data = {
        "id": current_artist.id,
        "name": current_artist.name,
        "genres": current_artist.genres,
        # "address": current_artist.address,
        "city": current_artist.city,
        "state": current_artist.state,
        "phone": current_artist.phone,
        "website": current_artist.website_link,
        "facebook_link": current_artist.facebook_link,
        "seeking_talent": current_artist.looking_for_venue,
        "seeking_description": current_artist.seeking_description,
        "image_link": current_artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    # data1 = {
    #     "id": 4,
    #     "name": "Guns N Petals",
    #     "genres": ["Rock n Roll"],
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "326-123-5000",
    #     "website": "https://www.gunsnpetalsband.com",
    #     "facebook_link": "https://www.facebook.com/GunsNPetals",
    #     "seeking_venue": True,
    #     "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    #     "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    #     "past_shows": [
    #         {
    #             "venue_id": 1,
    #             "venue_name": "The Musical Hop",
    #             "venue_image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
    #             "start_time": "2019-05-21T21:30:00.000Z",
    #         }
    #     ],
    #     "upcoming_shows": [],
    #     "past_shows_count": 1,
    #     "upcoming_shows_count": 0,
    # }
    # data2 = {
    #     "id": 5,
    #     "name": "Matt Quevedo",
    #     "genres": ["Jazz"],
    #     "city": "New York",
    #     "state": "NY",
    #     "phone": "300-400-5000",
    #     "facebook_link": "https://www.facebook.com/mattquevedo923251523",
    #     "seeking_venue": False,
    #     "image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    #     "past_shows": [
    #         {
    #             "venue_id": 3,
    #             "venue_name": "Park Square Live Music & Coffee",
    #             "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #             "start_time": "2019-06-15T23:00:00.000Z",
    #         }
    #     ],
    #     "upcoming_shows": [],
    #     "past_shows_count": 1,
    #     "upcoming_shows_count": 0,
    # }
    # data3 = {
    #     "id": 6,
    #     "name": "The Wild Sax Band",
    #     "genres": ["Jazz", "Classical"],
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "432-325-5432",
    #     "seeking_venue": False,
    #     "image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #     "past_shows": [],
    #     "upcoming_shows": [
    #         {
    #             "venue_id": 3,
    #             "venue_name": "Park Square Live Music & Coffee",
    #             "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #             "start_time": "2035-04-01T20:00:00.000Z",
    #         },
    #         {
    #             "venue_id": 3,
    #             "venue_name": "Park Square Live Music & Coffee",
    #             "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #             "start_time": "2035-04-08T20:00:00.000Z",
    #         },
    #         {
    #             "venue_id": 3,
    #             "venue_name": "Park Square Live Music & Coffee",
    #             "venue_image_link": "https://images.unsplash.com/photo-1485686531765-ba63b07845a7?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=747&q=80",
    #             "start_time": "2035-04-15T20:00:00.000Z",
    #         },
    #     ],
    #     "past_shows_count": 0,
    #     "upcoming_shows_count": 3,
    # }
    # data = list(filter(lambda d: d["id"] == artist_id, [data1, data2, data3]))[0]
    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):

    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)

    artist = {
        "id": artist_id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.looking_for_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
    }

    # artist = {
    #     "id": 4,
    #     "name": "Guns N Petals",
    #     "genres": ["Rock n Roll"],
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "326-123-5000",
    #     "website": "https://www.gunsnpetalsband.com",
    #     "facebook_link": "https://www.facebook.com/GunsNPetals",
    #     "seeking_venue": True,
    #     "seeking_description": "Looking for shows to perform at in the San Francisco Bay Area!",
    #     "image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    # }
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    try:
        form = ArtistForm(request.form)
        artist = Artist.query.get(artist_id)
        artist.name = form.name.data
        artist.phone = form.phone.data
        artist.state = form.state.data
        artist.city = form.city.data
        artist.genres = form.genres.data
        artist.image_link = form.image_link.data
        artist.facebook_link = form.facebook_link.data
        artist.website_link = form.website_link.data
        artist.looking_for_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data

        db.session.commit()
        flash("The Artist " + request.form["name"] + " has been successfully updated!")
    except:
        db.session.rollback()
        flash("An Error has occured and the update unsucessful")
    finally:
        db.session.close()

    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):

    new_venue = Venue.query.get(venue_id)
    form = VenueForm(obj=new_venue)
    venue = {
        "id": venue_id,
        "name": new_venue.name,
        "genres": new_venue.genres,
        "address": new_venue.address,
        "city": new_venue.city,
        "state": new_venue.state,
        "phone": new_venue.phone,
        "website": new_venue.website_link,
        "facebook_link": new_venue.facebook_link,
        "seeking_talent": new_venue.looking_for_talent,
        "seeking_description": new_venue.seeking_description,
        "image_link": new_venue.image_link,
    }

    # venue = {
    #     "id": 1,
    #     "name": "The Musical Hop",
    #     "genres": ["Jazz", "Reggae", "Swing", "Classical", "Folk"],
    #     "address": "1015 Folsom Street",
    #     "city": "San Francisco",
    #     "state": "CA",
    #     "phone": "123-123-1234",
    #     "website": "https://www.themusicalhop.com",
    #     "facebook_link": "https://www.facebook.com/TheMusicalHop",
    #     "seeking_talent": True,
    #     "seeking_description": "We are on the lookout for a local artist to play every two weeks. Please call us.",
    #     "image_link": "https://images.unsplash.com/photo-1543900694-133f37abaaa5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=400&q=60",
    # }
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    try:
        form = VenueForm()
        venue = Venue.query.get(venue_id)
        name = VenueForm.name.data

        venue.name = name
        venue.genres = form.genres.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.facebook_link = form.facebook_link.data
        venue.website_link = form.website_link.data
        venue.image_link = form.image_link.data
        venue.looking_for_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data

        db.session.commit()
        flash("Venue " + name + "has been updated")
    except:
        db.session.rollback()
        flash("An error occured while trying to update Venue")
    finally:
        db.session.close()

    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    try:
        form = ArtistForm(request.form)
        artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=form.genres.data,
            website_link=form.website_link.data,
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data,
            looking_for_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data,
        )

        db.session.add(artist)
        db.session.commit()
        flash("Artist " + request.form["name"] + " was successfully listed!")
    except:
        db.session.rollback()
        flash(
            "An error ocurred, Artist " + request.form["name"] + " could not be listed"
        )
        print(sys.exc_info())
    finally:
        db.session.close()
    # on successful db insert, flash success
    # flash("Artist " + request.form["name"] + " was successfully listed!")
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    shows = Show.query.order_by(db.desc(Show.start_time))
    data = []

    for show in shows:
        result = {
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time)),
        }
        data.append(result)

    # data = [
    #     {
    #         "venue_id": 1,
    #         "venue_name": "The Musical Hop",
    #         "artist_id": 4,
    #         "artist_name": "Guns N Petals",
    #         "artist_image_link": "https://images.unsplash.com/photo-1549213783-8284d0336c4f?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=300&q=80",
    #         "start_time": "2019-05-21T21:30:00.000Z",
    #     },
    #     {
    #         "venue_id": 3,
    #         "venue_name": "Park Square Live Music & Coffee",
    #         "artist_id": 5,
    #         "artist_name": "Matt Quevedo",
    #         "artist_image_link": "https://images.unsplash.com/photo-1495223153807-b916f75de8c5?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=334&q=80",
    #         "start_time": "2019-06-15T23:00:00.000Z",
    #     },
    #     {
    #         "venue_id": 3,
    #         "venue_name": "Park Square Live Music & Coffee",
    #         "artist_id": 6,
    #         "artist_name": "The Wild Sax Band",
    #         "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #         "start_time": "2035-04-01T20:00:00.000Z",
    #     },
    #     {
    #         "venue_id": 3,
    #         "venue_name": "Park Square Live Music & Coffee",
    #         "artist_id": 6,
    #         "artist_name": "The Wild Sax Band",
    #         "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #         "start_time": "2035-04-08T20:00:00.000Z",
    #     },
    #     {
    #         "venue_id": 3,
    #         "venue_name": "Park Square Live Music & Coffee",
    #         "artist_id": 6,
    #         "artist_name": "The Wild Sax Band",
    #         "artist_image_link": "https://images.unsplash.com/photo-1558369981-f9ca78462e61?ixlib=rb-1.2.1&ixid=eyJhcHBfaWQiOjEyMDd9&auto=format&fit=crop&w=794&q=80",
    #         "start_time": "2035-04-15T20:00:00.000Z",
    #     },
    # ]
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    try:
        show = Show(
            artist_id=request.form["artist_id"],
            venue_id=request.form["venue_id"],
            start_time=request.form["start_time"],
        )
        db.session.add(show)
        db.session.commit()
        flash("Show was successfully listed!")
    except:
        db.session.rollback()
        flash("An error occurred. Show could not be listed.")
        print(sys.exc_info())
    finally:
        db.session.close()
    # on successful db insert, flash success
    # flash("Show was successfully listed!")
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(
        Formatter("%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]")
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")


# ----------------------------------------------------------------------------#
# Utils
# ----------------------------------------------------------------------------#
def futureShowsCheck(shows):
    future_shows = []
    current_date = datetime.now()
    for show in shows:
        if show.start_time > current_date:
            future_shows.append(show)
    return future_shows


def pastShowsCheck(shows):
    past_shows = []
    current_date = datetime.now()
    for show in shows:
        if show.start_time <= current_date:
            past_shows.append(show)
    return past_shows


# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
