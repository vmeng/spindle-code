#!/bin/sh

# Find path to this script
if [[ $0 == /* ]] ; then
    DIR=$(dirname "$0")
else
    DIR=$(dirname "${PWD}/${0#./}")
fi
source "$DIR/conf.sh" || exit 1

# Define default SPINDLE_DIR
if [[ -z "$SPINDLE_DIR" ]] ; then
    SPINDLE_DIR="$DIR/demo"
fi

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
CELERYCAM_LOG="$LOG_DIR/celerycam.log"
CELERY_PID_FILE="$LOG_DIR/celery.pid"

# Run in the right virtual environment
source "$VIRTUALENV/bin/activate" || exit 1

postgres() {
    case "$1" in
        start)
            echo '* Starting postgres:'
            su "$PGUSER" -c "pg_ctl -l $PGLOG -D $PGDATA start"
            ;;

        stop)
            echo '* Stopping postgres:'
            su "$PGUSER" -c "pg_ctl -D $PGDATA stop"
            ;;

        stopfast)
            echo '* Stopping postgres fast:'
            su "$PGUSER" -c "pg_ctl -l $PGLOG -D $PGDATA -m fast stop"
            ;;

        *)
            echo '* Bad command "'$1'". Specify one of "start", "stop", "stopfast"'
            ;;
    esac
}

apache() {
    case "$1" in 
        start)
            echo '* Starting apache:'
            "$APACHECTL" restart
            ;;

        stop)
            echo '* Stopping apache:'
            "$APACHECTL" stop
            ;;

        *) echo '* Bad command "'$1'". Specify one of "start", "stop".'
            ;;
    esac
}


celery() {
    case "$1" in
        start)            
            echo '* Starting Sphinx celery worker: '
            nohup "$SPINDLE_DIR/manage.py" celery worker \
                --settings=celery_sphinx_settings --autoreload -Q sphinx -E \
                --loglevel=info </dev/null >"$CELERY_SPHINX_LOG" 2>&1 &
            echo $! | tee "$CELERY_PID_FILE"

            echo '* Starting local celery worker:'
            nohup "$SPINDLE_DIR/manage.py" celery worker \
                --settings=celery_local_settings --autoreload -Q local,celery -E \
                --loglevel=info </dev/null >"$CELERY_LOCAL_LOG" 2>&1 &
            echo $! | tee -a "$CELERY_PID_FILE"

            echo '* Starting celerycam monitor:'
            nohup "$SPINDLE_DIR/manage.py" celerycam \
                </dev/null >"$CELERYCAM_LOG" 2>&1 &
            echo $! | tee -a "$CELERY_PID_FILE"
            ;;

        stop)
            if [ -f "$CELERY_PID_FILE" ] ; then
                echo '* Stopping celery workers and celerycam:  '

                for pid in $(cat "$CELERY_PID_FILE") ; do
                    echo $pid
                    kill -15 $pid
                    while kill -0 $pid ; do sleep 1 ; done
                done
            fi
            ps ax | grep celery
            ;;

        restart)
            celery stop
            celery start
            ;;
    esac
}



main() {
    case "$1" in
        start)
            postgres start
            celery start
            if [ "$2" = dev ] ; then
                "$SPINDLE_DIR/manage.py" runserver
            else 
                apache start            
            fi
            ;;

        stop)
            celery stop
            apache stop
            postgres stop
            ;;
        
        postgres)
            shift
            postgres "$@"
            ;;

        apache)
            shift
            apache "$@"
            ;;
        
        celery)
            shift
            celery "$@"
            ;;

        *)
            echo 'Bad command: "'$1'".

Usage: 
   run_spindle.sh conf | start | stop |
      postgres (start|stop|stopfast) |
      apache (start|stop)
      celery (start|stop|restart)'
            exit 1
            ;;
    esac
}


main "$@"
