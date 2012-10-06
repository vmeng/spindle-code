from django.core.management.base import NoArgsCommand, CommandError
from spindle.models import Item

class Command(NoArgsCommand):
    help = 'Make archive copies of all items currently stored in the database.'

    def handle_noargs(self, *args, **options):
        total = i = 0.0

        total = Item.objects.count()
        self.stderr.write('Archiving {} items in database\n\n'.format(total)) 
        
        for obj in Item.objects.all():
            i += 1
            self.stderr.write(u'{:5.0f} {:3.1f}% {}\n'.format(
                    i, i/total * 100, obj))
            obj.archive()
            
        self.stderr.write('Archive complete\n\n')
