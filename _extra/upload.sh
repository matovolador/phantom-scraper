#!/bin/bash
scp -r instruments.csv root@<machine-ip>:/var/www/flask_app/flask_app || echo "Problem uploading file."
read -p "Enter any key to exit." continue