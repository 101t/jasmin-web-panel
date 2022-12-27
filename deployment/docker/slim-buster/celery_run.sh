#!/bin/bash

cd $JASMIN_HOME

celery -A main.taskapp worker -l info --autoscale=10,3