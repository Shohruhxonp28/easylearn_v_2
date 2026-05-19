"""Management command: python manage.py setup_demo"""
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Create demo data: admin, bots, categories, questions, arena, sample users'

    def handle(self, *args, **kwargs):
        from apps.accounts.models import User
        from apps.questions.models import Category, Question, QuestionOption
        from apps.matches.models import BotProfile
        from apps.arenas.models import Arena

        self.stdout.write('🚀 Setting up EduComp demo data...\n')

        # Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123',
                                          full_name='Admin User')
            self.stdout.write(self.style.SUCCESS('✅ Admin: admin / admin123'))
        else:
            self.stdout.write('   Admin already exists')

        # Demo students
        demo_users = [
            ('alice', 'Alice Smith', 1250, 15, 5, 2),
            ('bob', 'Bob Jones', 1100, 8, 10, 3),
            ('carol', 'Carol White', 1400, 22, 8, 1),
        ]
        for username, full_name, rating, wins, losses, draws in demo_users:
            if not User.objects.filter(username=username).exists():
                u = User.objects.create_user(username, password='demo123', full_name=full_name)
                u.rating = rating
                u.wins = wins
                u.losses = losses
                u.draws = draws
                u.save()
                self.stdout.write(self.style.SUCCESS(f'✅ User: {username} / demo123'))

        # Bots
        for name, level, initial in [('EasyBot','easy','EB'),('MediumBot','medium','MB'),('HardBot','hard','HB')]:
            BotProfile.objects.get_or_create(name=name, defaults={'level':level,'avatar_initial':initial})
        self.stdout.write(self.style.SUCCESS('✅ Bot profiles'))

        # Categories
        cats_data = [
            ('Mathematics','📐','Math problems and puzzles'),
            ('Science','🔬','Physics, Chemistry, Biology'),
            ('History','📜','World history and events'),
            ('Geography','🌍','Countries, capitals, maps'),
            ('Literature','📚','Books, authors, and poetry'),
            ('Technology','💻','IT, programming, tech'),
        ]
        cats = {}
        for name, icon, desc in cats_data:
            c, _ = Category.objects.get_or_create(name=name, defaults={'icon':icon,'description':desc})
            cats[name] = c
        self.stdout.write(self.style.SUCCESS(f'✅ {len(cats)} categories'))

        # Questions
        questions_data = [
            ('Mathematics','2 + 2 = ?','What is 2 plus 2?','single','easy',5,
             [('4',True),('3',False),('5',False),('22',False)],'Basic addition'),
            ('Mathematics','12 × 12 = ?','Calculate 12 multiplied by 12.','single','medium',10,
             [('144',True),('124',False),('148',False),('132',False)],'12 × 12 = 144'),
            ('Mathematics','√144 = ?','Square root of 144.','single','medium',10,
             [('12',True),('14',False),('11',False),('13',False)],'12 × 12 = 144'),
            ('Mathematics','Select all prime numbers','Which of these are prime?','multiple','hard',15,
             [('7',True),('11',True),('9',False),('15',False)],'7 and 11 are prime'),
            ('Mathematics','x² = 64, x = ?','Solve for x.','single','medium',10,
             [('8',True),('6',False),('4',False),('32',False)],'8² = 64'),
            ('Science','Chemical symbol for water?','H₂O is...','single','easy',5,
             [('H₂O',True),('CO₂',False),('O₂',False),('NaCl',False)],'Water = 2 Hydrogen + 1 Oxygen'),
            ('Science','Speed of light (approx)?','Light travels at...','single','medium',10,
             [('300,000 km/s',True),('150,000 km/s',False),('299 km/s',False),('3,000 km/s',False)],'~299,792 km/s'),
            ('Science','Gas giants in our solar system?','Select all gas giants.','multiple','hard',15,
             [('Jupiter',True),('Saturn',True),('Mars',False),('Earth',False)],'Jupiter and Saturn'),
            ('Science','Boiling point of water at sea level?','In Celsius.','single','easy',5,
             [('100°C',True),('90°C',False),('120°C',False),('80°C',False)],'Water boils at 100°C'),
            ('History','When did WWII end?','Year of victory.','single','easy',5,
             [('1945',True),('1944',False),('1918',False),('1939',False)],'1945, Germany & Japan surrendered'),
            ('History','First US President?','The founding father president.','single','easy',5,
             [('George Washington',True),('Abraham Lincoln',False),('Thomas Jefferson',False),('John Adams',False)],'Washington served 1789-1797'),
            ('History','Which wars were in the 20th century?','Select all.','multiple','hard',15,
             [('World War I',True),('World War II',True),('Napoleon Wars',False),('Seven Years War',False)],'WWI 1914, WWII 1939'),
            ('Geography','Capital of France?','The French capital.','single','easy',5,
             [('Paris',True),('Lyon',False),('Marseille',False),('Nice',False)],'Paris since 987'),
            ('Geography','Largest continent by area?','The biggest landmass.','single','medium',10,
             [('Asia',True),('Africa',False),('Europe',False),('America',False)],'Asia: 44.5 million km²'),
            ('Geography','Longest river in the world?','Flowing mightily...','single','medium',10,
             [('Nile',True),('Amazon',False),('Yangtze',False),('Mississippi',False)],'Nile: ~6,650 km'),
            ('Literature','Who wrote Romeo and Juliet?','A famous English playwright.','single','easy',5,
             [('William Shakespeare',True),('Charles Dickens',False),('Jane Austen',False),('Mark Twain',False)],'Shakespeare, ~1595'),
            ('Literature','Who wrote 1984?','Dystopian classic.','single','medium',10,
             [('George Orwell',True),('Aldous Huxley',False),('Ray Bradbury',False),('H.G. Wells',False)],'Orwell published 1984 in 1949'),
            ('Technology','CPU stands for?','Core computing component.','single','easy',5,
             [('Central Processing Unit',True),('Computer Power Unit',False),('Central Power User',False),('Core Processing Unit',False)],'CPU = Central Processing Unit'),
            ('Technology','Which are programming languages?','Select all.','multiple','medium',10,
             [('Python',True),('Java',True),('HTML',False),('CSS',False)],'Python and Java are languages; HTML/CSS are markup/style'),
            ('Technology','What does HTTP stand for?','Web protocol.','single','easy',5,
             [('HyperText Transfer Protocol',True),('High Transfer Text Protocol',False),('HyperText Transmission Protocol',False),('Hyper Transfer Text Protocol',False)],'HTTP = HyperText Transfer Protocol'),
        ]

        created = 0
        for cat_name, title, body, qtype, diff, pts, options, expl in questions_data:
            q, new = Question.objects.get_or_create(
                title=title,
                defaults={'category':cats[cat_name],'body':body,'question_type':qtype,
                          'difficulty':diff,'points':pts,'explanation':expl,'status':'published'}
            )
            if new:
                for i,(text,correct) in enumerate(options):
                    QuestionOption.objects.create(question=q,text=text,is_correct=correct,order=i)
                created += 1
        self.stdout.write(self.style.SUCCESS(f'✅ {created} questions created ({Question.objects.count()} total)'))

        # Arena
        now = timezone.now()
        if not Arena.objects.filter(status='live').exists():
            math_cat = cats['Mathematics']
            Arena.objects.create(
                title='⚡ Math & Science Live Arena',
                description='Battle live opponents on Math and Science questions!',
                category=math_cat,
                start_time=now - timedelta(minutes=5),
                end_time=now + timedelta(hours=1),
                duration_minutes=60,
                questions_per_match=5,
                status='live',
                difficulty='medium',
                bot_enabled=True,
            )
            Arena.objects.create(
                title='📜 History & Geography Challenge',
                description='Test your world knowledge!',
                start_time=now + timedelta(hours=1),
                end_time=now + timedelta(hours=2),
                duration_minutes=60,
                questions_per_match=5,
                status='upcoming',
                difficulty='easy',
                bot_enabled=True,
            )
            self.stdout.write(self.style.SUCCESS('✅ 2 arenas created (1 live, 1 upcoming)'))

        self.stdout.write('\n' + self.style.SUCCESS('🎉 Demo setup complete!'))
        self.stdout.write('   🌐 Homepage:  http://localhost:8000/')
        self.stdout.write('   ⚙️  Admin:     http://localhost:8000/admin/')
        self.stdout.write('   👤 Login:     admin / admin123')
        self.stdout.write('   🎮 Demo users: alice / demo123, bob / demo123, carol / demo123')
