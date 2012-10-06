import datetime, sys
# DEBUG AND INTERNAL HELP METHODS ==============================================================
# Eventually this should be all replaced by Django logging I presume...
DEBUG = False
ERROR_CACHE = ""
ERROR_LOG = None


def __init__():
    global DEBUG
    DEBUG = False
    global ERROR_CACHE
    ERROR_CACHE = ""
    global ERROR_LOG
    ERROR_LOG = None
    return None

def onscreen(error_str):
    "Basic optional debug function. Print the string if enabled"
    global DEBUG
    if DEBUG:
        sys.stderr.write('DEBUG:{0}\n'.format(error_str))
    return None

def errorlog(error_str=""):
    "Write errors to a log file cache"
    global ERROR_CACHE
    ERROR_CACHE += 'ERROR:{0}\n'.format(error_str)
    return None

def errorlog_start(path_to_file):
    global ERROR_LOG
    try:
        ERROR_LOG = open(path_to_file,'a')
    except IOError:
        sys.stderr.write("WARNING: Could not open existing error file. New file being created")
        ERROR_LOG = open(path_to_file,'w')

    errorlog("Log started at {0:%Y-%m-%d %H:%M:%S}\n".format(datetime.datetime.utcnow()))
    sys.stderr.write("Writing errors to: {0}\n\n".format(path_to_file))
    return None

def errorlog_save():
    "Write errors to a log file"
    global ERROR_CACHE, ERROR_LOG
    if ERROR_LOG:
        ERROR_LOG.write(ERROR_CACHE)
        ERROR_CACHE = ""
    else:
        sys.stderr.write("WARNING!! No Error Log file has been created\n\n{0}".format(ERROR_CACHE))
    return None

def errorlog_stop():
    global ERROR_LOG
    if ERROR_LOG:
        errorlog("Log ended at {0:%Y-%m-%d %H:%M:%S}\n".format(datetime.datetime.utcnow()))
        errorlog_save()
        ERROR_LOG.close()
    else:
        sys.stderr.write("WARNING!! No Error Log file has been created")
    return None
