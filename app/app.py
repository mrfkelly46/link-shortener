#!/usr/bin/env python3
import sys
import json
import ssl
import random
import pymysql
from flask import Flask, jsonify, abort, request, make_response, session, redirect
from flask_restful import reqparse, Resource, Api
from flask_session import Session
from ldap3 import Server, Connection, ALL
from ldap3.core.exceptions import *
from urllib.parse import urlparse

import settings


app = Flask(__name__)
app.secret_key = settings.SECRET_KEY
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_NAME'] = 'cs3103_group_o_session'
app.config['SESSION_COOKIE_DOMAIN'] = settings.APP_HOST
Session(app)


####################################################################################

def get_db_conn():
    return pymysql.connect(
        settings.DB_HOST,
        settings.DB_USER,
        settings.DB_PASS,
        settings.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

def get_short():
    # Get a random string (while there is a chance of collision this is good enough)
    chars = '23456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKMNPQRSTUVWXYZ'
    length = 8
    while True:
        # Generate a short string
        short = ''.join(random.choice(chars) for i in range(length))
        # If we generate one with no letters, re-roll
        if not short.isdigit():
            break
    return short

####################################################################################

def registered(func):
    def wrapper(*args, **kwargs):
        if 'username' not in session or 'users_id' not in session:
            abort(401)
        else:
            return func(*args, **kwargs)
    return wrapper

####################################################################################

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'status': 'Bad request'}), 400)

@app.errorhandler(401)
def unauthorized(error):
    return make_response(jsonify({'status': 'Unauthorized'}), 401)

@app.errorhandler(403)
def forbidden(error):
    return make_response(jsonify({'status': 'Forbidden'}), 403)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'status': 'Resource not found'}), 404)

####################################################################################

class Root(Resource):
    def get(self):
        return app.send_static_file('index.html')


class Login(Resource):
    def post(self):
        # POST: Login to the API
        if not request.json:
            abort(400)

        parser = reqparse.RequestParser()
        try:
            parser.add_argument('username', type=str, required=True)
            parser.add_argument('password', type=str, required=True)
            params = parser.parse_args()
        except:
            abort(400)

        username = params['username']
        password = params['password']

        if username != session.get('username') or 'users_id' not in session:
            try:
                ldapServer = Server(host=settings.LDAP_HOST)
                ldapConnection = Connection(
                    ldapServer,
                    raise_exceptions=True,
                    user='uid='+username+', ou=People,ou=fcs,o=unb',
                    password=password
                )
                ldapConnection.open()
                ldapConnection.start_tls()
                ldapConnection.bind()

                conn = get_db_conn()
                cursor = conn.cursor()
                cursor.callproc('getUser', (username,))
                user = cursor.fetchone()
                conn.commit()
            except LDAPException:
                abort(403)
            except:
                abort(500)
            finally:
                ldapConnection.unbind()

            session['username'] = username
            session['users_id'] = user['id']

        return make_response(jsonify({'status': 'success'}), 200)

    @registered
    def get(self):
        # GET: Check if logged in to the API
        # Just piggyback off the @registered decorator; if we get into this function, then we are logged in
        return make_response(jsonify({'status': 'success'}), 200)

    def delete(self):
        # DELETE: Logout of the API
        if 'username' in session or 'users_id' in session:
            session.pop('username')
            session.pop('users_id')
        else:
            abort(401)

        return make_response(jsonify({'status': 'success'}), 200)


class AdminGetUsers(Resource):
    @registered
    def get(self):
        # GET: Returns all users
        if session['username'] not in settings.ADMINS:
            abort(403)

        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            cursor.callproc('getAllUsers')
            users = cursor.fetchall()
        except:
            abort(500)
        finally:
            cursor.close()
            conn.close()

        response = {
            'status': 'success',
            'users': users,
        }

        return make_response(jsonify(response), 200)


class AdminGetLinks(Resource):
    @registered
    def get(self):
        # GET: Returns all shortened link records
        if session['username'] not in settings.ADMINS:
            abort(403)

        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            cursor.callproc('getAllLinks')
            links = cursor.fetchall()
        except:
            abort(500)
        finally:
            cursor.close()
            conn.close()

        response = {
            'status': 'success',
            'links': links,
        }

        return make_response(jsonify(response), 200)

class Links(Resource):
    @registered
    def get(self):
        # GET: Returns all shortened link records belonging to the logged in user
        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            cursor.callproc('getLinksByUser', (session['users_id'],))
            links = cursor.fetchall()
        except:
            abort(500)
        finally:
            cursor.close()
            conn.close()

        response = {
            'status': 'success',
            'links': links,
        }

        return make_response(jsonify(response), 200)

    @registered
    def post(self):
        # POST: Creates a new shortened link
        if not request.json:
            abort(400)

        parser = reqparse.RequestParser()
        try:
            parser.add_argument('original_link', type=str, required=True)
            params = parser.parse_args()
        except:
            abort(400)

        original = params['original_link']
        parsed = urlparse(original)
        if not parsed or not parsed.netloc:
            abort(400)
        
        shortened = get_short()

        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            cursor.callproc('addLink', (session['users_id'], original, shortened))
            new_link = cursor.fetchone()
            conn.commit()
        except:
            abort(500)
        finally:
            cursor.close()
            conn.close()

        new_link = {
            'id': new_link['new_id'],
            'original_link': original,
            'shortened_link': shortened,
            'users_id': session['users_id'],
        }
        response = {
            'status': 'success',
            'link': new_link,
        }

        return make_response(jsonify(response), 201)


class Link(Resource):
    @registered
    def get(self, linkID):
        # GET: Retrieves a shortened link record
        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            cursor.callproc('getLink', (linkID,))
            link = cursor.fetchone()
        except:
            abort(500)
        finally:
            cursor.close()
            conn.close()

        if link is None:
            abort(404)
        if link['users_id'] != session['users_id']:
            abort(403)

        response = {
            'status': 'success',
            'link': link,
        }

        return make_response(jsonify(response), 200)

    @registered
    def patch(self, linkID):
        # PATCH: Updates a shortened link record
        if not request.json:
            abort(400)

        parser = reqparse.RequestParser()
        try:
            parser.add_argument('original_link', type=str, required=True)
            params = parser.parse_args()
        except:
            abort(400)

        new_original = params['original_link']
        parsed = urlparse(new_original)
        if not parsed or not parsed.netloc:
            abort(400)

        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            cursor.callproc('getLink', (linkID,))
            link = cursor.fetchone()
            if link is not None and link['users_id'] == session['users_id']:
                cursor.callproc('updateLink', (linkID, new_original))
                conn.commit()
        except:
            abort(500)
        finally:
            cursor.close()
            conn.close()

        if link is None:
            abort(404)
        if link['users_id'] != session['users_id']:
            abort(403)

        return make_response(jsonify({'status': 'success'}), 200)

    @registered
    def delete(self, linkID):
        # DELETE: Deletes a shortened link record
        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            cursor.callproc('getLink', (linkID,))
            link = cursor.fetchone()
            if link is not None and link['users_id'] == session['users_id']:
                cursor.callproc('deleteLink', (linkID,))
                conn.commit()
        except:
            abort(500)
        finally:
            cursor.close()
            conn.close()

        if link is None:
            abort(404)
        if link['users_id'] != session['users_id']:
            abort(403)

        return make_response(jsonify({'status': 'success'}), 204)


class Shortened(Resource):
    def get(self, shortened):
        # GET: Redirects from the shortened link to the original link
        try:
            conn = get_db_conn()
            cursor = conn.cursor()
            cursor.callproc('reverseLink', (shortened,))
            link = cursor.fetchone()
        except:
            abort(500)
        finally:
            cursor.close()
            conn.close()

        if link is None:
            abort(404)

        return redirect(link['original_link'], code=302)
    
####################################################################################

api = Api(app)
api.add_resource(Root, '/')
api.add_resource(Login, '/login')
api.add_resource(AdminGetUsers, '/admin/users')
api.add_resource(AdminGetLinks, '/admin/links')
api.add_resource(Links, '/links')
api.add_resource(Link, '/links/<int:linkID>')
api.add_resource(Shortened, '/l/<string:shortened>')

####################################################################################

if __name__ == "__main__":
    context = ('cert.pem', 'key.pem')
    app.run(
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        ssl_context=context,
        debug=settings.APP_DEBUG)

