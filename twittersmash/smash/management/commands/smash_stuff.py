import twitter
import datetime
import feedparser
import re
import pytz
import string
from django.core.management.base import BaseCommand
from smash.models import Feed, TwitterAccount, Message

twit_re = re.compile(r'^(?P<username>\S+): (?P<message>.*)$')

class Command(BaseCommand):
    help = "Loops through feeds and determines if messages need to be sent to any twitter accounts"

    def handle(self, *args, **options):
        # Get list of TwitterAccounts
		accounts = TwitterAccount.objects.all().filter(active=True)
		for account in accounts:
			keywords = account.philter.lower().split(',')
			keywords = map(string.strip, keywords)
			api = twitter.Api(username=account.username, password=account.password)
			print "Checking %s" % (account,)
			feed_list = account.feeds.all()
			for f in feed_list:
				print " - %s" % (f,)
				# Get list of feeds who'se last_update + polling_rate is less than now
				if f.last_checked == None or f.last_checked + \
				datetime.timedelta(minutes=f.polling_rate) < datetime.datetime.now():
					# Update timestamp
					f.last_checked = datetime.datetime.now()
					f.save()
					print "   * Pulling feed"
					# Pull each feed
					d = feedparser.parse(f.url)
					# Loop through feed
					for entry in d['entries']:
						guid = entry.id
						tweeted = entry.updated_parsed
						message = twit_re.search(entry.title).groups()[1]
						#print guid, tweeted, message
						tweeted_dt = datetime.datetime(
							tweeted[0], 
							tweeted[1], 
							tweeted[2], 
							tweeted[3], 
							tweeted[4], 
							tweeted[5], 
							tzinfo=pytz.utc
						)
						
						msg, created = Message.objects.get_or_create(
							guid=guid, 
							twitteraccount=account, 
							defaults={
								'feed': f, 
								'tweeted': tweeted_dt,
								'message': message,
								'twitteraccount': account,
						})
						
						if created:
							# Wasn't already in the db
							for keyword in keywords:
								if keyword in message.lower():
									# We need to send it to the twitter account
									try:
										status = api.PostUpdate(message)
										msg.sent_to_twitter = True
										msg.save()
										print "   * Sent to Twitter (%s)" % (keyword,)
									except e:
										print "   - Failed to send to twitter (%s)" % (e,)
				else:
					print "   * Checked within the last %s minutes" % (f.polling_rate)	
					# If twitter account has a filter check each item for the filter text
						# If the message isn't in the Messages table, add it
							# Send message to twitter account
					# If the message isnt in the Messages table, add it
						# Send message to twitter account
		