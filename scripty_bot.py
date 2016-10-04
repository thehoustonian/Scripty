import random
import re
# import argparse
import json
import yaml
import operator
import os
import time
import sys
from twisted_bot import Bot, BotFactory
from twisted.internet import reactor
from twisted.internet.error import AlreadyCalled

"""
Need to add a lock so you can't start playback on another script while one is already being played
Maybe add high scores for people who have viewed the most things/viewing history, etc?
Total time spent showing things?
Pie-in-the sky dream: set up a dropbox folder for scripts to pull from/take a web address
"""

class ScriptyBot(Bot):

    def __init__(self):
        self.bot_name = "Scripty"
        self.help_message = ("Hello, I am a friendly bot created by Trey Franklin during the Fall 2016 coop term "
                             "to read things to you in an IRC room while you avoid your responsibilities. "
                             "I am pretty straightforward to use, especially right now since I'm brand new.\n"
                             "When issuing commands, please use the syntax 'Scripty, *command*' "
                             "Supported commands include 'help', 'play *filename*', 'list files', "
                             "'stop'. I probably contain some unintended 'features' as well.")

    def sanity_check(self):
        if 'scripts' not in os.listdir(os.getcwd()):
            print("YOU DINGUS YOU DON'T HAVE A 'scripts' FOLDER!!!!!!")
            return False
        else:
            return True
    
    def command(self, prefix, msg):
        if "help" in msg:
            self.info(prefix, "help")
        
        else:
            return

    def info(self, prefix, info_type):
        for line in self.responses.get(info_type):
            self.msg(prefix, line)
    
    def respond(self, response):
        self.say(self.factory.channel, response)
    
    # custom method to alert other channels about activity
    def alert(self):
        for channel in self.factory.other_channels:
            self.say(channel, "A viewing will start soon in: %s" % self.factory.channel)

    def get_available_files(self):
        if not self.sanity_check():
            self.respond("Sorry fam, not happening. I don't have a folder for that!'")
        else:
            return os.listdir(os.getcwd() + '/scripts')
    
    def format_file(self, filename):
        file = open(os.getcwd() + '/scripts/' + filename)
        max_line_length = 150
        string_array = []
        for line in file:
            line.replace('\xef\xbf\xbd', "'")
            """while len(line) > max_line_length:
                string_array.append(line[:max_line_length])
                line = line[max_line_length:]"""
            string_array.append(line)
        file.close()
        return string_array

    def play(self, filename):
        #would be nice to support folders of things, but not right now
        if not self.sanity_check():
            self.respond("Look, you really should create that 'scripts' folder I mentioned...")
        elif filename not in self.get_available_files():
            self.respond("Hate to say it, but I don't have that one! Have you double-checked the filename?")
        else:
            self.respond("Coming right up! Get your popcorn.")
            self.alert()
            self.display_title(filename)
            self.respond("Formatting file")
            formatted_file = self.format_file(filename)
            self.respond("Done formatting, enjoy the show!")
            self.respond("3...")
            self.respond("2...")
            self.respond("1!")
            wait_time = 0
            for line in formatted_file:
                reactor.callLater(wait_time, self.respond, line)
                wait_time += 4
            reactor.callLater(wait_time, self.respond, "Show's over! Hope you enjoyed it!")
            reactor.callLater(wait_time, self.display_title, "Nothing")

    # custom method to set the channel topic
    def display_title(self, title):
        self.topic(self.factory.channel, "Now Showing:       %s" %title)

    def parse_message(self, message):
        """
        Right now, Scripty won't support many commands.
        Hopefully this will change in the future :-)
        """
        message = message.split()
        length = len(message)
        if length <= 0 or self.bot_name not in message[0]:
            return None
        
        if length == 1:
            self.respond('Yes, can I help you?')
        
        elif ('help' or 'Help' or 'HELP') in message[1]:
            self.respond(self.help_message)
        
        elif ('play') in message[1]:
            if length == 2:
                self.respond("Hey, you've gotta give me a filename to play!")
                self.respond("Here are the available options: %s" %self.get_available_files())
            else:
                self.respond("Got it!")
                self.play(message[2])
        elif 'stop' in message[1]:
            for call_object in reactor.getDelayedCalls():
                try:
                    call_object.cancel()
                except AlreadyCalled:
                    continue
            self.respond('Fine, be that way. I can really feel the love :/')
            self.display_title('Nothing...')
        elif 'list files' in message:
            self.respond("Alright, here's what I have: ")
            self.respond(self.get_available_files())
        else:
            self.respond("Uhhh, what'd you say?")
                

    # needed by Twisted to react to content in the channel
    def privmsg(self, user, channel, msg):
        if not user or channel != self.factory.channel:
            return
        else:
            self.parse_message(msg)

    def signedOn(self):
        for channel in self.factory.other_channels:
            self.join(channel)
        self.join(self.factory.channel)
        print "Signed on as %s." % self.nickname
        self.say(self.factory.channel, "Hello everyone, I'm alive!")
        if not self.sanity_check():
            self.response("Whoever is hosting me is a dingus and didn't give me a 'scripts' folder")
            sys.exit()
        self.display_title('Nothing.')


class ScriptyBotFactory(BotFactory):
    protocol = ScriptyBot

    def __init__(self, channel, nickname, other_channels):
        BotFactory.__init__(self, channel, nickname)
        self.other_channels = other_channels

if __name__ == "__main__":
    host = "coop.test.adtran.com"
    port = 6667
    chan = "theater" #"THE_MAGIC_CONCH_ROOM" "test" "main"
    other_channels = ["#main", "#THE_MAGIC_CONCH_ROOM"]
    reactor.connectTCP(host, port, ScriptyBotFactory("#" + chan, "Scripty", other_channels))
    reactor.run()
