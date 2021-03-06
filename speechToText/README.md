### SPINDLE Speech to text automatic transcription

We used CMU Sphinx4 during the [SPINDLE project](http://blogs.oucs.ox.ac.uk/openspires/category/spindle/) to generate automatic transcription of our podcasts. Please find below the instructions to set up CMU Sphinx4 in Large Vocabulary Continuous Speech Recognition mode. 

- Download and install the source version of [CMU Sphinx4](http://sourceforge.net/projects/cmusphinx/files/sphinx4/1.0%20beta6/sphinx4-1.0beta6-src.zip/download) to $SPHINX_INSTALL_DIRECTORY. Instructions can be found at their [website](http://cmusphinx.sourceforge.net/wiki/sphinx4:howtobuildand_run_sphinx4) and here is the access to their [forums](http://cmusphinx.sourceforge.net/wiki/communicate/).
- Download HUB4 [acoustic](http://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/US%20English%20HUB4%20Acoustic%20Model/) and [language models](http://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/US%20English%20HUB4%20Language%20Model/).
- Copy HUB4 acoustic models to the $SPHINX_INSTALL_DIRECTORY/models/acustic/ directory and HUB4 language models to the $SPHINX_INSTALL_DIRECTORY/models/language/ directory. 
- Download [CMUdict dictionary](https://cmusphinx.svn.sourceforge.net/svnroot/cmusphinx/trunk/cmudict/sphinxdict/) version cmudict.0.7a_SPHINX_40. Copy the file to $SPHINX_INSTALL_DIRECTORY/models/dictionary/.
- Modify Transcriber.java from src/apps/edu/cmu/sphinx/demo/transcriber/Transcriber.java to show the time stamps for each word in the automatic transcription.

    Original:
    
            String resultText = result.getBestResultNoFiller();
            System.out.println(resultText);

    Modified:
    
            if (result != null){
                System.out.println(result.getTimedBestResult(true, true));
            }

- Download config.xml and copy to src/apps/edu/cmu/sphinx/demo/transcriber/config.xml
- Compile from the installation directory:

        ant 

- Run the Transcriber.jar program from $SPHINX_INSTALL_DIRECTORY:

        java -mx800m -jar bin/Transcriber.jar file.wav

- The audio .wav file should be 16khz, 16-bit, 1 channel, little-endian signed integer (lpcm)

## Notes

- Configuration may not be optimal. You could adjust some of the parameters (beams, language model weight, word insertion penalty, etc) depending on your task.

- We used different models to generate our automatic transcription such as a British English dictionary. If you are interested in it please get in contact with us. 

## Links 

- Our blog: [SPINDLE project](http://blogs.oucs.ox.ac.uk/openspires/category/spindle/) 
- CMU Sphinx: [http://www.cmusphinx.org](http://www.cmusphinx.org)
- Similar project: [Truly Madly Wordly](http://trulymadlywordly.blogspot.co.uk/2011/12/sphinx4-speech-recognition-results-for.html) uses CMU Sphinx4 for the transcription of university lectures. 

## Tags

 #spindle #openspires #ukoer #oerri 

     
