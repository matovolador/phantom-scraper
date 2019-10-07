#!/usr/bin/python3.6
## ---- Author ---- ##
## Matias Garafoni - matias.garafoni@gmail.com ##
## ---------------------##
from flask import Flask, request, render_template, Response, abort, send_file, jsonify, redirect, url_for, send_from_directory, session, make_response, flash, g
from werkzeug.utils import secure_filename
from flask_cors import CORS
import pymysql.cursors
import json, os, requests
import random, string
import sys
import csv
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
# general origin request access:
CORS(app)
# specific
#cors = CORS(app, resources={r"/*": {"origins": "*"}})  # documentation here: https://pypi.org/project/Flask-Cors/

UPLOAD_FOLDER = "/var/www/flask_app/flask_app/static/files/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/")
def index():
    return "success",202

@app.route("/health")
def health():
        my_file = Path(app.config['UPLOAD_FOLDER']+"errors_calendar.txt")
        my_file2 = Path(app.config["UPLOAD_FOLDER"]+"errors_instruments.txt")

        time_error = ""
        # check timestamps:
        with open(app.config['UPLOAD_FOLDER']+"data_calendar.json",encoding='utf-8') as f:
                file_output = json.load(f)
                time_dif = (datetime.now() - datetime.strptime(file_output['data_time'].split(".")[0],"%Y-%m-%d %H:%M:%S")).total_seconds() /60/60/24
                # print("Checking time dif with calendar")
                # print(time_dif)
                if 'data_time' in file_output and time_dif > 2:
                        time_error = "The time detected on data_calendar.json and/or data_instruments.json is bigger than 2 days."

        # check timestamps:
        with open(app.config['UPLOAD_FOLDER']+"data_instruments.json", encoding='utf-8') as f:
                file_output = json.load(f)
                time_dif = (datetime.now() - datetime.strptime(file_output['data_time'].split(".")[0],"%Y-%m-%d %H:%M:%S")).total_seconds() /60/60/24
                # print("Checking time dif with instruments")
                # print(time_dif)
                if 'data_time' in file_output and time_dif > 2:
                        time_error = "The time detected on data_calendar.json and/or data_instruments.json is bigger than 2 days."

        if my_file.is_file() or my_file2.is_file():
        # errors exist:
                return jsonify({
                        "message":"Errors with script execution where detected. Please check <url>/files/errors.txt or <url>/files/errors_instruments.txt to see what those are."+"\n"+time_error,
                        "errors": 1
                })
        elif time_error:
                return jsonify({
                        "message": time_error,
                        "errors":1
                })
        else:
                return jsonify({
                        "message":"Everything looks good.",
                        "errors": 0
                })

@app.route("/files/<path:filename>",methods=["GET"])
def get_file(filename):
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'],filename=filename,cache_timeout=-1)
    except Exception as e:
        return jsonify({"message":"File not found","error":str(e)})

if __name__ == "__main__":
        app.secret_key = 'secret123'
        app.run(debug=True,port="5858")
