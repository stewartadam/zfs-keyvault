import flask
import flask_sqlalchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = flask.Flask(__name__)
app.config.from_object('zkvgateway.config.DefaultConfig')
app.config.from_envvar('CONFIG_FILE', silent=True)

limiter = Limiter(
  app,
  key_func=get_remote_address
)

db = flask_sqlalchemy.SQLAlchemy(app)

from . import models
from . import views
