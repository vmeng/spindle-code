from django.core.management.base import NoArgsCommand, CommandError

class Command(NoArgsCommand):
    help = 'Download all Koemei data for testing'

    def handle_noargs(self, *args, **options):
        from spindle.transcribe.koemei.koemei_api import koemei_api_request as api
        import requests
        from requests.auth import HTTPBasicAuth
        from spindle.models import Item
        import urlparse
        import os.path
        from django.db.models import Q
        from django.conf import settings

        media = api('GET', 'media')
        items = media.findall('mediaItem')

        auth = HTTPBasicAuth(settings.SPINDLE_KOEMEI_USERNAME, settings.SPINDLE_KOEMEI_PASSWORD)

        for item in items:
            url = item.find('fileName').text
            print url

            basename = os.path.basename(urlparse.urlparse(url).path)

            records = Item.objects.filter(Q(audio_url__endswith = basename) |
                                          Q(video_url__endswith = basename))
            print records

            if records:
                filename = str(records[0].id)
            else:
                filename = basename + ".xml"

            dirname = os.path.join(settings.SPINDLE_KOEMEI_TEST_DATA_DIR,
                                   filename)
            outfile = open(dirname, "w")

            if(item.find('currentTranscript')):
                print dirname, "\n\n"
                script_url = item.find('currentTranscript')[0].attrib['href']
                resp = requests.get(script_url, auth = auth)
                outfile.write(resp.content)
