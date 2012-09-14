### SPINDLE Speech to text automatic transcription

Please find below the instructions to set up CMU Sphinx4 in Large Vocabulary Continuous Speech Recognition mode. We used different models for our automatic transcription such as a British English dictionary. If you would be interested in it please get in contact with us. 

- Download and install the source version of [CMU Sphinx4](http://sourceforge.net/projects/cmusphinx/files/sphinx4/1.0%20beta6/sphinx4-1.0beta6-src.zip/download) to $SPHINX_INSTALL_DIRECTORY. Instructions can be found at their [website](http://cmusphinx.sourceforge.net/wiki/sphinx4:howtobuildand_run_sphinx4) and here is the access to their [forums](http://cmusphinx.sourceforge.net/wiki/communicate/).
- Download HUB4 [acoustic](http://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/US%20English%20HUB4%20Acoustic%20Model/) and [language models](http://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/US%20English%20HUB4%20Language%20Model/).
- Copy HUB4 acoustic models to the directory $SPHINX_INSTALL_DIRECTORY/models/acustic and HUB4 language models to the directory $SPHINX_INSTALL_DIRECTORY/models/language. 
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

- Run Transcriber.jar from bin/Transcriber.jar:

        java -mx800m -jar bin/Transcriber.jar file.wav

- NOTE: the audio .wav file should be 16khz, 16-bit, 1 channel, little-endian signed integer (lpcm)

## Tags

 #spindle #openspires #ukoer #oerri 

     
