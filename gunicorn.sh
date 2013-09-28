#!/bin/bash
set -e
VENV=/home/crimeweather/sites/civic-json-app
LOGFILE=$VENV/run/gunicorn.log
LOGDIR=$(dirname $LOGFILE)
NUM_WORKERS=3
# user/group to run as
USER=crimeweather
GROUP=crimeweather
cd $VENV/checkouts/civic-json-worker
source $VENV/bin/activate
source /home/crimeweather/.zshenv
test -d $LOGDIR || mkdir -p $LOGDIR
exec $VENV/bin/gunicorn -w $NUM_WORKERS --daemon --bind 127.0.0.1:6666 --user=$USER --group=$GROUP --log-level=info --log-file=$LOGFILE 2>>$LOGFILE app:app
