import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key_here'
    SQLALCHEMY_DATABASE_URI = postgresql://postgres:FogLdsGbyuRXtlcMXoErOCssOoEyiNTh@autorack.proxy.rlwy.net:52876/railway
    SQLALCHEMY_TRACK_MODIFICATIONS = False
