## Introduction

Welcome to the SPINDLE project [[blog](http://blogs.oucs.ox.ac.uk/openspires/category/spindle/)]
[[website](http://openspires.oucs.ox.ac.uk/spindle/)] code
repository. This repository contains three main folders:

- [**keywords**](https://github.com/ox-it/spindle-code/tree/master/keywords):
this directory contains `keywords.py`, a python script
developed during the SPINDLE project that generates keywords from a
text.  It has been used during the project to
[generate keywords from automatic transcriptions]
(http://blogs.oucs.ox.ac.uk/openspires/2012/09/12/spindle-automatic-keyword-generation-step-by-step/).

- [**speechToText**](https://github.com/ox-it/spindle-code/tree/master/speechToText):
this directory contains instructions to set up CMU Sphinx4 in Large
Vocabulary Continuous Speech Recognition mode. It also contains a
config.xml file for the Transcribe.java application.

- [**web**](https://github.com/ox-it/spindle-code/tree/master/web): A
prototype web interface for the above two systems, which can also do
other useful things relating to podcasts, transcription and speech to
text:

  - import audio and video podcasts from RSS, matching up audio and
    video recordings of the same material where possible
  - import transcripts from formats including SRT/WebVTT, Adobe
    Premiere XMP files, and others 
  - edit imported transcripts in sync with the audio or video, or
    start with a blank transcript and create one from scratch
  - queue items for automated speech-to-text transcription, either
    using the freely available CMU Sphinx4 system or interfacing
    with the Koemei commercial ASR service (http://koemei.com)
  - automatically extract keywords for items with associated
    transcript text
  - export edited captions and transcripts in SRT, plain text, and
    HTML form
  - publish exported captions and transcripts to a directory of static
    files, with control over which items are published and in what
    form
  - publish a copy of the incoming RSS feed, including automatically
    extracted keywords as `<category>` tags

Some of these features are closer to completion than others. The web
interface is written in Python with the Django framework. See
[web/README.md](https://github.com/ox-it/spindle-code/tree/web/README.md)
for more details on how to install and test it.
  

## Tags

 #spindle #openspires #ukoer #oerri 

     
