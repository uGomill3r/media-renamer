from flask import Blueprint, render_template
from config import MEDIA_PATH

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    return render_template('home.html', initial_path=str(MEDIA_PATH))
