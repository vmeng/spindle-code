#!/bin/sh

source ./conf.sh || exit 1

# Run as "run_spindle.sh conf" to print out configuration
if [[ "$1" == conf ]] ; then
    echo "LOG_DIR=$LOG_DIR"
    echo "VIRTUALENV=$VIRTUALENV"
    echo "SPINDLE_DIR=$SPINDLE_DIR"
    echo "PGLOG=$PGLOG"
    echo "PGDATA=$PGDATA"
    echo "PGUSER=$PGUSER"
    echo "APACHECTL=$APACHECTL"
    exit 0
fi

# Sanity check
if [[ -z "$LOG_DIR" || -z "$VIRTUALENV" || -z "$SPINDLE_DIR" || -z "$PGLOG" \
    || -z "$APACHECTL" || -z "$PGDATA" ]] ; then
    echo 'Some variables not set. Check conf.sh'.
    exit 1
fi

# Find celery logfiles and PID file
CELERY_SPHINX_LOG="$LOG_DIR/celery.sphinx.log"
CELERY_LOCAL_LOG="$LOG_DIR/celery.local.log"
CELERY_PID_FILE="$LOG_DIR/celery.pid"

# Run in the right virtual environment
source "$VIRTUALENV/bin/activate" || exit 1

case "$1" in
    start)
        echo '* Starting postgres:'
        sudo su "$PGUSER" -c "pg_ctl -l $PGLOG -D $PGDATA start"

        echo '* Starting apache:'
        sudo "$APACHECTL" restart

        echo '* Starting Sphinx celery worker: '
        nohup "$SPINDLE_DIR/manage.py" celery worker \
            --settings=settings --autoreload -Q sphinx \
            --loglevel=info </dev/null >"$CELERY_SPHINX_LOG" 2>&1 &
        echo $! | tee "$CELERY_PID_FILE"

        echo '* Starting Sphinx local worker:'
        nohup "$SPINDLE_DIR/manage.py" celery worker \
            --settings=settings --autoreload -Q local,celery \
            --loglevel=info </dev/null >"$CELERY_LOCAL_LOG" 2>&1 &
        echo $! | tee -a "$CELERY_PID_FILE"
        ;;

    stop)
        echo '* Stopping apache:'
        sudo "$APACHECTL" stop

        if [ -f "$CELERY_PID_FILE" ] ; then
            echo '* Stopping celery workers:  '

            for pid in $(cat "$CELERY_PID_FILE") ; do
                echo $pid
                kill -15 $pid
                while kill -0 $pid ; do sleep 1 ; done
            done
        fi
        ps ax | grep celery

        echo '* Stopping postgres:'
        sudo su "$PGUSER" -c "pg_ctl -D $PGDATA stop"
        ;;

    apacherestart)
        echo '* Restarting apache:'
        sudo "$APACHECTL" restart
        ;;
    
    pgstart)
        echo '* Starting postgres:'
        sudo su "$PGUSER" -c "pg_ctl -l $PGLOG -D $PGDATA start"
        ;;

    pgstopfast)
        echo '* Stopping postgres fast:'
        sudo su "$PGUSER" -c "pg_ctl -l $PGLOG -D $PGDATA -m fast stop"
        ;;

    *)
        echo 'Bad command: "'$1'".
Specify one of: conf, stop, start, pgstart, pgstopfast, apacherestart'
        ;;
esac
