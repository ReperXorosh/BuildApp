from flask import Blueprint, request, url_for, redirect, render_template, session
from flask_login import login_required

from ..models.objects import Objects

objects = Blueprint('objects', __name__)

