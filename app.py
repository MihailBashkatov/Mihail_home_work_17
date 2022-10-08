# Импорт необходимых библиотек

from flask import Flask, request
from flask_restx import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from marshmallow import Schema, fields

# Формирование приложения и его конфигурация
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['RESTX_JSON'] = {'ensure_ascii': False, 'indent': 4}


# Формирование базы данных
db = SQLAlchemy(app)

# Формирования API REST
api = Api(app)

# Формирование нэймспейссов
ns_movies = api.namespace('movies')
ns_directors = api.namespace('directors')
ns_genres = api.namespace('genres')


# Формирование класса Movie
class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.String(255))
    trailer = db.Column(db.String(255))
    year = db.Column(db.Integer)
    rating = db.Column(db.Float)
    genre_id = db.Column(db.Integer, db.ForeignKey("genre.id"))
    genre = db.relationship("Genre")
    director_id = db.Column(db.Integer, db.ForeignKey("director.id"))
    director = db.relationship("Director")


# Формирование класса Director
class Director(db.Model):
    __tablename__ = 'director'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


# Формирование класса Genre
class Genre(db.Model):
    __tablename__ = 'genre'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))


# Формирование схемы Director
class DirectorSchema(Schema):
    id = fields.Integer()
    name = fields.String()


# Формирование схемы Genre
class GenreSchema(Schema):
    id = fields.Integer()
    name = fields.String()


# Формирование схемы Movie
class MovieSchema(Schema):
    id = fields.Integer(dump_only=True)
    title = fields.String()
    description = fields.String()
    trailer = fields.String()
    year = fields.Integer()
    rating = fields.Float()
    genre = fields.Nested(GenreSchema, only=['name'])
    director = fields.Pluck(field_name='name', nested=DirectorSchema)


# Формирование сереилизаторов по всем схемам для одного элемента и для списка
movie_schema = MovieSchema()
movies_schema = MovieSchema(many=True)
director_schema = DirectorSchema()
directors_schema = DirectorSchema(many=True)
genre_schema = GenreSchema()
genres_schema = GenreSchema(many=True)


@ns_movies.route('/')
class MoviesView(Resource):
    def get(self):
        """ Формирование представления для получения фильмов"""

        movies = Movie.query.all()
        requested_director_id = request.args.get("director_id")
        requested_genre_id = request.args.get("genre_id")
        requested_page = request.args.get("page")

        # При квери-запросе по страницам выводится 5 фильмов/страница
        if requested_page:
            movies = Movie.query.limit(5).offset(int(requested_page) * 5 - 5)

        # При квери-запросе по director
        if requested_director_id:
            movies = Movie.query.filter(Movie.director_id == requested_director_id).all()

        # При квери-запросе по genre
        if requested_genre_id:
            movies = Movie.query.filter(Movie.genre_id == requested_genre_id).all()

        # При квери-запросе по director и genre
        if requested_genre_id and requested_genre_id:
            movies = Movie.query.filter(Movie.genre_id == requested_genre_id,
                                        Movie.director_id == requested_director_id)

        # Если запрос возвращает пустой список, то ошибка
        if len(movies_schema.dump(movies)) == 0:
            return '', 404
        return movies_schema.dump(movies), 200


    def post(self):
        """
        Формирование представления для добавления нового фильма
        """

        json_req = request.json
        movie_added = Movie(**json_req)
        db.session.add(movie_added)
        db.session.commit()
        return '', 201


@ns_movies.route('/<int:mid>')
class MovieView(Resource):
    def get(self, mid):
        """
        Формирование представления для получения фильма по id
        В случае отсутствия фильма - ошибка
        """

        try:
            movie = Movie.query.filter(Movie.id == mid).one()
            return movie_schema.dump(movie), 200
        except Exception as e:
            return f'{e}', 404


@ns_directors.route('/')
class DirectorsView(Resource):
    def post(self):
        """
        Формирование представления для добавления нового режиссера
        """

        json_req = request.json
        director_added = Director(**json_req)
        db.session.add(director_added)
        db.session.commit()
        return '', 201


@ns_directors.route('/<int:did>')
class DirectorView(Resource):
    def get(self, did):
        """
        Формирование представления для получения режиссера по id
        В случае отсутствия фильма - ошибка
        """

        try:
            director = Director.query.filter(Director.id == did).one()
        except Exception as e:
            return f'{e}', 404
        return director_schema.dump(director)

    def put(self, did):
        """
        Формирование представления для изменения данных режиссера по id
        В случае отсутствия режиссера - ошибка
        """

        director = Director.query.get(did)
        if not director:
            return '', 404

        json_req = request.json
        director.name = json_req.get("name")
        db.session.add(director)
        db.session.commit()
        return '', 204

    def delete(self, did):
        """
        Формирование представления для удалени режиссера по id
        В случае отсутствия режиссера - ошибка
        """

        director = Director.query.get(did)
        if not director:
            return '', 404
        db.session.delete(director)
        db.session.commit()
        return '', 204


@ns_genres.route('/')
class GenresView(Resource):
    def post(self):
        """
        Формирование представления для добавления нового режиссера
        """

        json_req = request.json
        genre_added = Genre(**json_req)
        db.session.add(genre_added)
        db.session.commit()
        return '', 201


@ns_genres.route('/<int:did>')
class GenreView(Resource):
    def get(self, did):
        """
        Формирование представления для получения жанра по id
        В случае отсутствия жанра - ошибка
        """

        try:
            genre = Genre.query.filter(Genre.id == did).one()
        except Exception as e:
            return f'{e}', 404
        return genre_schema.dump(genre)

    def put(self, did):
        """
        Формирование представления для изменения данных жанра по id
        В случае отсутствия жанра - ошибка
        """

        genre = Genre.query.get(did)
        if not genre:
            return '', 404

        json_req = request.json
        genre.name = json_req.get("name")
        db.session.add(genre)
        db.session.commit()
        return '', 204

    def delete(self, did):
        """
        Формирование представления для удалени жанра по id
        В случае отсутствия жанра - ошибка
        """
        genre = Genre.query.get(did)
        if not genre:
            return '', 404
        db.session.delete(genre)
        db.session.commit()
        return '', 204


if __name__ == '__main__':
    app.run(port=22000)