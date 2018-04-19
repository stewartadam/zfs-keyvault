import os
import sys

APP_INSTALL_PATH='/var/www/myapp'
VIRTUALENV_PATH='/var/www/myapp/virtualenv'

activate_this = os.path.join(VIRTUALENV_PATH, 'bin/activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

sys.path.insert(0, APP_INSTALL_PATH)
from myapp import app as application
