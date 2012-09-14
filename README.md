# Spindle

## Overview

This is a prototype of a system for using speech-to-text for podcast
indexing and transcription.

## Installation

Spindle is a Django application, and requires recent versions of
Django and Python (>= 2.7) to run. All the dependencies are managed
through the [pip](http://pypi.python.org/pypi/pip) Python package
manager, using the `requirements.txt` file.

While not required, it's probably worth installing
[virtualenv](http://www.virtualenv.org/en/latest/index.html) and
[virtualenvwrapper](http://www.doughellmann.com/projects/virtualenvwrapper/)
to keep the library dependencies separate.

Using `virtualenvwrapper`, the following commands should be enough
to install Spindle:

    mkvirtualenv spindle
    workon spindle
    git clone https://github.com/ox-it/spindle
    cd spindle
    pip install -r requirements.txt

## Configuring

You'll need to configure some local settings for databases, file
paths, etc. in the `demo/local_settings.py` file.

First, do

    cp demo/local_settings.py.template demo/local_settings.py
    
At a minimum, you'll need to set up a database for Django to use. The
easiest option is an SQLite database, which doesn't require a separate
server or extra configuration. In the new `local_settings.py`, change
the lines following `DATABASE` to something like the following:

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/path/to/database/file.db',     
            ....

The database file can be located anywhere, and will be created
automatically (provided the containing directory exists).

To set up the database, do the following:

    cd demo
    ./manage.py syncdb
    
(this step will also prompt you to create a user name and password)
and then,

    ./manage.py migrate sitetree
    ./manage.py migrate spindle
    ./manage.py loaddata spindle/fixtures/sitetree.json

At this point you should be able to run the development server by doing

    ./manage.py runserver
    
and loading [http://localhost:8000/](http://localhost:8000/) in your
web browser.

## Other settings

It's easiest to import podcasts into Spindle by pulling them from an
RSS feed. Set `SPINDLE_SCRAPE_RSS_URL` in `local_settings.py` to
enable this; then you can run `./manage.py spindle_scrape` to import
data, or use the "New item" page within the web interface.

Some computationally-heavy parts of Spindle run asynchronously, using
the [Celery](http://celeryproject.org/) framework. These tasks will
run in their own process. To start it, do

    ./manage.py celery worker --settings=settings

Celery also allows distributing tasks over a network by using the
[RabbitMQ](http://www.rabbitmq.com) message queue; configuring this is
outside the scope of this document.

### CMU Sphinx integration

- Download and install the source version of [CMU Sphinx4](http://sourceforge.net/projects/cmusphinx/files/sphinx4/1.0%20beta6/sphinx4-1.0beta6-src.zip/download) to $SPHINX_INSTALL_DIRECTORY. Instructions can be found at their [website](http://cmusphinx.sourceforge.net/wiki/sphinx4:howtobuildand_run_sphinx4) and here is the access to their [forums](http://cmusphinx.sourceforge.net/wiki/communicate/).
- Download HUB4 [acoustic](http://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/US%20English%20HUB4%20Acoustic%20Model/) and [language models](http://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/US%20English%20HUB4%20Language%20Model/).
- Copy acoustic models to the directory $SPHINX_INSTALL_DIRECTORY/models/acustic and the language models to the directory $SPHINX_INSTALL_DIRECTORY/models/language. 
- Modify Transcriber.java from src/apps/edu/cmu/sphinx/demo/transcriber/Transcriber.java to show the time stamps for each word in the automatic transcription.

    Original:
    
            String resultText = result.getBestResultNoFiller();
            System.out.println(resultText);

    Modified:
    
            if (result != null){
                System.out.println(result.getTimedBestResult(true, true));
            }

- Download spindleSpeechToText/config.xml and copy to src/apps/edu/cmu/sphinx/demo/transcriber/config.xml
- Compile from the installation directory:

        ant 

- Run Transcriber.jar from bin/Transcriber.jar:

        java -mx800m -jar bin/Transcriber.jar file.wav

- NOTE: the audio .wav file should be 16khz, 16-bit, 1 channel, little-endian signed integer (lpcm)


- See `SPINDLE_SPHINX_DIRECTORY` variable.

### Koemei integration 

Spindle has some experimental support for integration with
[Koemei](www.koemei.com), an online speech-to-text service. To enable
this, you will need to sign up for a Koemei account through their web
page; then set the `SPINDLE_KOEMEI_USERNAME` and
`SPINDLE_KOEMEI_PASSWORD` configuration variables in
`local_settings.py`.

### Public directories

Spindle can export transcripts in plain text, HTML and VTT formats,
and publish an annotated copy of the incoming RSS feed which includes
keywords automatically extracted from transcript text. See the
variables `SPINDLE_PUBLIC_DIRECTORY`, `SPINDLE_PUBLIC_URL`,
`SPINDLE_PUBLISH_RSS_NAME` in `local_settings.py`.

Publishing currently has to be done from the command line:

    ./manage.py spindle_publish all
