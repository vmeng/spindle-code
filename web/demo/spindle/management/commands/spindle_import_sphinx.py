from django.core.management.base import BaseCommand, CommandError
from spindle.models import Item, Track, Speaker
from spindle.transcribe.sphinx.reader import read_clips
import os
from django.db.models import Q

TRACK_NAME = 'Sphinx transcript'

class Command(BaseCommand):
    args = '<index filename> <data directory>'
    help = 'Import Sphinx output into the database'

    def handle(self, *args, **options):
        index_filename = args[0]
        data_dir = args[1]
        
        url_not_found = []
        file_not_found = []

        items = Item.objects.bulk_fetch()

        index = open(index_filename)
        total_count = 0
        for line in index: total_count += 1

        index.seek(0,0)
        for idx, line in enumerate(index):
            url, filename = line.split(" ")
            filename = filename.strip()

            self.stderr.write(u'\n{:4.1f}% {}\n'.format(
                    100 * float(idx) / total_count, url))

            try:
                item = items.audio[url]                                       
            except KeyError:
                item = items.video[url]
            except KeyError:
                self.stderr.write(u"No item found -- not imported\n\n".format(url)) 
                url_not_found.append(url)
                continue

            self.stderr.write(u'{} {}\n'.format(
                    item.id, item.name))
            if item.track_set.filter(name__exact = TRACK_NAME).count():
                self.stderr.write("Already imported\n\n")
                continue

            track = Track(item=item, name=TRACK_NAME)
            track.save()
            
            speaker = Speaker(track=track, name="Speaker 1")
            speaker.save()

            path = os.path.join(data_dir, filename)

            try:
                sphinx_output = open(path)
            except:
                self.stderr.write(u"Unable to open {}".format(path))
                file_not_found.append(path)
                continue

            for clip in read_clips(open(os.path.join(data_dir, filename)),
                                   speaker = speaker):
                self.stderr.write(u"{:6.1f} {:6.1f} {}\n".format(
                        clip.intime, clip.outtime, clip.caption_text))
                clip.track = track
                clip.save()

            item.archive()
            self.stderr.write('\n\n')

        if url_not_found:
            self.stderr.write("{} URLs not found in database:\n".format(
                    len(url_not_found)))
            for url in url_not_found:
                self.stderr.write(u'\t{}\n'.format(url))

        if file_not_found:
            self.stderr.write("{} files not found:\n".format(
                    len(file_not_found)))
            for path in file_not_found:
                self.stderr.write(u'\t{}\n'.format(path))

            
