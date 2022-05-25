#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form, FlaskForm
from forms import *
from sqlalchemy.dialects.postgresql import ARRAY
from models import db, Artist, Venue, Show
from utils import format_datetime
import sys
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)
migrate = Migrate(app, db)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    venues = Venue.query.all()
    state_city = {}
    data = []
    for venue in venues:
        num_upcoming_shows = Show.query.filter(
            Show.venue_id == venue.id, Show.start_time >= datetime.now()).count()
        category_key = venue.city + venue.state
        if(state_city.get(category_key) != None):
            index_to_add = state_city[category_key]
            venue_list = data[index_to_add]['venues']
            venue_list.append({
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": num_upcoming_shows
            })
            data[index_to_add]['venues'] = venue_list
            continue
        data.append({
            "city": venue.city,
            "state": venue.state,
            "venues": [{
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": num_upcoming_shows
            }]
        })
        state_city[category_key] = len(data) - 1

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search = request.form.get('search_term')
    venues = Venue.query.filter(Venue.name.ilike(f'%{search}%')).all()
    response = {
        "count": len(venues),
        "data": venues,
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    if bool(venue) != True:
        flash('Venue ' + venue_id + ' does not exist')
        return render_template('pages/show_venue.html', venue=[])

    past_shows_tuple = db.session.query(Venue.id, Venue.name, Venue.image_link, Show.start_time).filter(
        Show.venue_id == venue_id, Show.start_time < datetime.now()).join(Venue).all()

    past_shows = []
    for show in past_shows_tuple:
        past_shows.append({
            'artist_id': show[0],
            'artist_name': show[1],
            'artist_image_link': show[2],
            'start_time': str(show[3]),
        })

    upcoming_shows_tuple = db.session.query(Artist.id, Artist.name, Artist.image_link, Show.start_time).filter(
        Show.venue_id == venue_id, Show.start_time >= datetime.now()).join(Artist).all()

    upcoming_shows = []
    for show in upcoming_shows_tuple:
        upcoming_shows.append({
            'artist_id': show[0],
            'artist_name': show[1],
            'artist_image_link': show[2],
            'start_time': str(show[3]),
        })

    past_shows_count = len(past_shows)
    upcoming_shows_count = len(upcoming_shows)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website_link,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": past_shows_count,
        "upcoming_shows_count": upcoming_shows_count
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    form = VenueForm()
    name = form.name.data
    city = form.city.data
    state = form.state.data
    address = form.address.data
    phone = form.phone.data
    image_link = form.image_link.data
    genres = form.genres.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    seeking_talent = form.seeking_talent.data
    seeking_description = form.seeking_description.data

    form_valid = form.validate_on_submit()
    if form_valid:
        error = False
        try:
            newVenue = Venue(
                name=name,
                city=city,
                state=state,
                address=address,
                phone=phone,
                image_link=image_link,
                genres=genres,
                facebook_link=facebook_link,
                website_link=website_link,
                seeking_talent=seeking_talent,
                seeking_description=seeking_description
            )
            db.session.add(newVenue)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()

        if error:
            flash('An error occurred. Venue ' + name + ' could not be listed.')
        else:
            flash('Venue ' + name + ' was successfully listed!')
    else:
        for field, message in form.errors.items():
            flash(field + ' - ' + str(message))
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    error = False
    try:
        venue = Venue.query.get(venue_id)
        db.session.delete(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if(error):
        flash('Error, Venue belongs to a show or venue does not exist')
    else:
        flash('Venue with id ' + venue_id + ' successfully deleted')

    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    artists = Artist.query.all()
    return render_template('pages/artists.html', artists=artists)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search = request.form.get('search_term')
    artist = Artist.query.filter(Artist.name.ilike(f'%{search}%')).all()
    response = {
        "count": len(artist),
        "data": artist,
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = Artist.query.get(artist_id)
    if bool(artist) != True:
        flash('Artist ' + artist_id + ' does not exist')
        return render_template('pages/show_artist.html', artist=[])

    past_shows_tuple = db.session.query(Venue.id, Venue.name, Venue.image_link, Show.start_time).filter(
        Show.artist_id == artist_id, Show.start_time < datetime.now()).join(Venue).all()

    past_shows = []
    for show in past_shows_tuple:
        past_shows.append({
            'venue_id': show[0],
            'venue_name': show[1],
            'venue_image_link': show[2],
            'start_time': str(show[3]),
        })

    upcoming_shows_tuple = db.session.query(Venue.id, Venue.name, Venue.image_link, Show.start_time).filter(
        Show.artist_id == artist_id, Show.start_time >= datetime.now()).join(Venue).all()

    upcoming_shows = []
    for show in upcoming_shows_tuple:
        upcoming_shows.append({
            'venue_id': show[0],
            'venue_name': show[1],
            'venue_image_link': show[2],
            'start_time': str(show[3]),
        })

    past_shows_count = len(past_shows)
    upcoming_shows_count = len(upcoming_shows)
    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website_link,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": past_shows_count,
        "upcoming_shows_count": upcoming_shows_count
    }

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    defaultVal = {
        'name': artist.name,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'image_link': artist.image_link,
        'genres': artist.genres,
        'facebook_link': artist.facebook_link,
        'website_link': artist.website_link,
        'seeeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description
    }
    form = ArtistForm(data=defaultVal)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    form = ArtistForm()
    error = False

    try:
        artist = Artist.query.get(artist_id)
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.image_link = form.image_link.data
        artist.genres = form.genres.data
        artist.facebook_link = form.facebook_link.data
        artist.website_link = form.website_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        flash('Error Updating artist ' + artist_id)
    else:
        flash('Artist was successfully Updated')
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get(venue_id)
    defaultVal = {
        'name': venue.name,
        'city': venue.city,
        'state': venue.state,
        'address': venue.address,
        'phone': venue.phone,
        'image_link': venue.image_link,
        'genres': venue.genres,
        'facebook_link': venue.facebook_link,
        'website_link': venue.website_link,
        'seeking_talent': venue.seeking_talent,
        'seeking_description': venue.seeking_description
    }
    form = VenueForm(data=defaultVal)

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm()
    error = False

    try:
        venue = Venue.query.get(venue_id)
        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.address = form.address.data
        venue.phone = form.phone.data
        venue.image_link = form.image_link.data
        venue.genres = form.genres.data
        venue.facebook_link = form.facebook_link.data
        venue.website_link = form.website_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        flash('Error Updating venue with id ' + venue_id)
    else:
        flash('Venue was successfully Updated')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    form = ArtistForm()
    name = form.name.data
    city = form.city.data
    state = form.state.data
    phone = form.phone.data
    image_link = form.image_link.data
    genres = form.genres.data
    facebook_link = form.facebook_link.data
    website_link = form.website_link.data
    seeking_venue = form.seeking_venue.data
    seeking_description = form.seeking_description.data

    form_valid = form.validate_on_submit()
    if form_valid:
        error = False
        data = {}
        try:
            newArtist = Artist(
                name=name,
                city=city,
                state=state,
                phone=phone,
                image_link=image_link,
                genres=genres,
                facebook_link=facebook_link,
                website_link=website_link,
                seeking_venue=seeking_venue,
                seeking_description=seeking_description
            )
            data['name'] = newArtist.name
            db.session.add(newArtist)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()

        if(error):
            flash('An error occurred. Artist ' +
                  data['name'] + ' could not be listed.')
        else:
            flash('Artist ' + data['name'] + ' was successfully listed!')

    else:
        for field, message in form.errors.items():
            flash(field + ' - ' + str(message))

    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    shows = db.session.query(
        Venue.id,
        Venue.name,
        Artist.id,
        Artist.name,
        Artist.image_link,
        Show.start_time,
    ).join(Artist).join(Venue).all()

    data = []

    for show in shows:
        data.append({
            'venue_id': show[0],
            'venue_name': show[1],
            'artist_id': show[2],
            'artist_name': show[3],
            'artist_image_link': show[4],
            'start_time': str(show[5])
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    form = ShowForm()
    artist_id = form.artist_id.data
    venue_id = form.venue_id.data
    start_time = form.start_time.data

    error = False

    try:
        newShow = Show(
            artist_id=artist_id,
            venue_id=venue_id,
            start_time=start_time
        )
        db.session.add(newShow)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if(error):
        flash('An error occurred. Show could not be listed.')
    else:
        flash('Show was successfully listed!')

    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
