from flask_login import LoginManager

from solawi.app import app
import solawi.models as models

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return models.User.get(user_id)