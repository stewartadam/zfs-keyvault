import flask
import flask_sqlalchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = flask.Flask(__name__)
limiter = Limiter(
  app,
  key_func=get_remote_address
)
app.config.from_object('zkvgateway.config.DefaultConfig')
app.config.from_pyfile('zfs-keyvault-gateway.cfg')

db = flask_sqlalchemy.SQLAlchemy(app)

from . import models
from . import views
