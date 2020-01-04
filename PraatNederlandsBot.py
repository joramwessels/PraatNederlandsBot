#!/usr/bin/env python

"""
PraatNederlandsBot.py:  Reddit bot reminding users of r/CirkelTrek to speak Dutch

    Searches r/CirkelTrek for comments containing one (or more) of the triggers,
    and responds to the comments' parent with one of the specified responses.
    No response will be posted if:
        1) the parent comment has already been replied to by the bot
        2) the parent comment was posted by the bot
        3) the trigger was part of a response by the bot
    Also corrects the use of "upvote" and "downvote" to their Dutch equivalents

"""

__authors__ = "Joram Wessels"
__version__ = "0.2"
__date__ = "30-12-2019"
__status__ = "prototype"

import praw
import re
import random
import time
import datetime

#--------------------------------------+
#                Content               |
#--------------------------------------+

# The case insensitive phrases that trigger the bot to leave one of the responses below
triggers = \
[
    "angelsaksisch gebrabbel",
    "a n g e l s a k s i s c h g e b r a b b e l",
    "!praatnederlands",
    "!angelsaksischgebrabbel"
]

# The possible responses when triggered (uses markdown)
responses = \
[
"Praat gewoon Nederlands.",
"Nederlands is ook best moeilijk",
"Ruik ik daar een Angelsaks?",
"Één of meerdere woorden uit dit bericht kon ik helaas niet in het Nederlandse woordenboek terugvinden. U bent bij deze een Angelsaks.",
"\"Nederlands, moederneuker! Spreekt u dat?\"\n\n~ Samuel L. Jacobszoon",
"###Probeer het de volgende keer in het Nederlands\n\nDeze boodschap werd u gebracht door De Nederlanse Taal.  \nDe Nederlandse Taal: *praat gewoon Nederlands*",
"Ik verzoek u eens een kijkje te nemen op deze webpagina: https://www.vandale.nl/",
"Als u het Nederlands nog niet machtig bent kunt u hier hulp vinden: https://www.inburgeren.nl/u-gaat-inburgeren/cursus-kiezen.jsp",
"Ik begrijp dat u hulp nodig heeft bij het leren van onze taal. Les 1: https://www.youtube.com/watch?v=yrrvscBeR9U",
"Geachtte heer/mevrouw,\n\nHet ministerie van Onderwijs, Cultuur en Wetenschap (OCW) heeft per september 2015 de verantwoordelijkheid gekregen van het kabinet om het aantal laaggeletterden in Nederland te verminderen. Uit de bovenstaande publicatie blijkt dat u tot deze groep behoort, en zijn wij daarom wettelijk genoodzaakt om maatregelen tegen u te nemen. De effectiefste methode om laggeletterdheid aan te pakken is analfabetische zuivering. Uw gegevens zijn bij deze doorgegeven aan de AIVD. Zij zullen de komende 2-4 weken onverwachts contact met u opnemen voor verdere afhandeling van dit proces.\n\nHoogachtend,\n\nIngrid van Engelshoven  \nMinister van OCW",
"Wie op Lashet wilt schryven  \nmaar het Nederlandsch niet spreekt  \nDient zwygzaem te blyven  \nals hij r/Cirkeltrek betreedt",
"Al spreek je Vlaams, Rotjeknors of Achterhoeks; we houden het hier wel in het Nederlands.",
"In **NEDERLAND** spreken wij gewoon **NEDERLANDS**!\n\n~ Frans Duits",
"Er zijn twee dingen in deze wereld die ik niet uit kan staan: mensen die niet tolerant zijn voor andermans cultuur... en de Angelsaksen\n\n~ Nigel Krachten",
"Ooooooh  \nU bent een vreemdeling  \nU bent een legale vreemdeling  \nU bent een Angelsaks op r/Cirkeltrek\n\n~ Prik",
"Excuseer. Ik kon uw paal niet horen onder het geluid van\n\n##BUITENLANDS GEBRABBEL",
"Ik ben Willem de Zwijger  \nDat is weliswaar een geuzennaam  \nFok je met m'n taal?  \nBreek ik binnen door je keukenraam  \nen neuk ik je moeder  \nsnuif poeder  \nneem haar op vakantie  \nSpanjool of Angelsaks\n\n##Jullie testen onze tolerantie",
"Voordat andere Rediteuren nu ook denken: \"Ik mag mijn speech in een andere taal houden,\" dat is echt niet de bedoeling. Het Nederlands is de voertaal op r/Cirkeltrek en dat wil ik graag zo houden.\n\n~ Khadija Arib  \nVoorzitter van de Tweede Kamer"
]

# A footer to let user know this is an automated response (uses markdown)
footer = "\n\n \n\n----------------------------------------------\n ^(Dit is een geautomatiseerde reactie. Geef mij een opwillem als ik een brave bot ben.)"



#--------------------------------------+
#               Settings               |
#--------------------------------------+

subredditName = "cirkeltrek"    # cirkeltrek / testingground4bots
onlyRespondToNewComments = True # Only respond to comments made after deployment
secondsSleepOnError = 60        # Errors thrown while posting are typically Rate Limit errors
maximumSleepIterations = 10     # To prevent infinite loops in case of other errors
correctAnglosaxon = True        # Leave witty remarks underneath non-Dutch comments/posts
correctToOpwillem = True        # Correct "upvote" and "downvote" to their Dutch equivalents


#--------------------------------------+
#                 Code                 |
#--------------------------------------+

reddit = praw.Reddit(
    client_id="-----------",
    client_secret="----------",
    user_agent="PraatNederlands 0.2",
    username="---------",
    password="---------"
)
subreddit = reddit.subreddit(subredditName)
bot_user_id = reddit.user.me().id
linkPrefix = "https://www.reddit.com"
logfilename = "PraatNederlandsBot.log"

def Log(message, precedeWithTimeStamp=False):
    """ Logs to stdio and file

        Input
            message:               The message to log
            precedeWithTimeStamp:  Whether to precede the log entry with a time stamp

    """
    logstring = ""
    if (precedeWithTimeStamp):
        logstring += datetime.datetime.now().strftime("%Y/%m/%d/%H:%M:%S") + '\t'
    logstring += message
    logfile = open(logfilename, 'a')
    logfile.write(logstring)
    logfile.close()
    print(logstring, end='')

def RespondToComment(comment, bot_reply):
    """ Responds to a comment/post and handles comment rate limit errors

        Input
            comment:   A `praw.models.Comment` or `praw.models.Submission` instance
            bot_reply: The comment the bot should leave

    """
    retryReply = True
    replyTries = 0
    while retryReply and replyTries < maximumSleepIterations:
        try:
            retryReply = False
            comment.reply(bot_reply)
        except praw.exceptions.PRAWException as e:
            # e is most likely a rate limit error
            Log(e, True)
            Log("\n")
            Log("Sleeping for %i seconds\n" %secondsSleepOnError, True)
            time.sleep(secondsSleepOnError)
            retryReply = True
            replyTries += 1 # don't retry forever

def AlreadyRepliedTo(comment):
    """ Checks if the bot has already replied to a comment/post

        Input
            comment: A `praw.models.Comment` or `praw.models.Submission` instance
        Returns
            A boolean indicating whether the bot has already responded
    
    """
    # Comments
    if (type(comment) == praw.models.Comment):
        comment.refresh()
        comments = comment.replies
    # Posts
    elif (type(comment) == praw.models.Submission):
        comments = comment.comments
    # Input should be one of the above types
    else:
        return
    # Checking the comment forest
    for reply in comments:
        if (reply.author and reply.author.id == bot_user_id):
            return True
    return False

def CheckCommentForBotTriggers(comment):
    """ Checks the comment for mentions of any of the triggers, and replies

        Input
            comment: A `praw.models.Comment` instance
    
    """
    for trigger in triggers:
        if re.search(trigger, comment.body, re.IGNORECASE):
            Log("found '%s'... " %trigger, True)

            # Don't get triggered by your own comments
            if (comment.author and comment.author.id == bot_user_id):
                Log("in my own comment\n")
                return
            
            # Don't respond to yourself
            parent = comment.parent()
            if (parent.author and parent.author.id == bot_user_id):
                Log("parent is my own comment\n")
                return

            # Don't comment if already replied to this comment/post
            if AlreadyRepliedTo(parent):
                Log("already replied\n")
                return
            
            # Leave a reply to the parent
            bot_reply = random.choice(responses) + footer
            RespondToComment(parent, bot_reply)
            Log("commented by: u/%s... " %comment.author.name)
            Log("replied to: ")
            Log(linkPrefix)
            Log(parent.permalink)
            Log("\n")
            
            return # stop checking all triggers

def CorrectUpvoteToOpwillem(comment):
    """ Checks for the use of "upvote" or "downvote" and corrects it

        Input
            comment: A `praw.models.Comment` instance

    """
    bot_reply = ""
    # Upvote
    if re.search("upvote", comment.body, re.IGNORECASE):
        Log("found 'upvote'... ", True)
        if (AlreadyRepliedTo(comment)):
            Log("already responded\n")
            return
        bot_reply = "Opwillem*"
    # Downvote
    elif re.search("downvote", comment.body, re.IGNORECASE):
        Log("found 'downvote'... ", True)
        if (AlreadyRepliedTo(comment)):
            Log("already responded\n")
            return
        bot_reply = "Neerfilips*"
    # Leaving the reply
    if (bot_reply != ""):
        RespondToComment(comment, bot_reply)
        Log("replied to: ")
        Log(linkPrefix)
        Log(comment.permalink)
        Log("\n")

def main():
    """ An infinite loop that listens to new (or old) comments on the subreddit
    """
    while True:
        Log("Execution started for subreddit '%s'.\n" %subredditName, True)
        Log("Press ctrl-C to stop (KeyBoardInterrupt).\n", True)
        try:
            # Iterate through all (new) CirkelTrek comments
            for comment in subreddit.stream.comments(skip_existing=onlyRespondToNewComments):
                if (correctAnglosaxon): CheckCommentForBotTriggers(comment)
                if (correctToOpwillem): CorrectUpvoteToOpwillem(comment)
        except praw.exceptions.PRAWException as e:
            # Log the error and restart the loop
            Log('\n')
            Log(e, True)
            Log("\n")
            Log("restarting...\n", True)
        except KeyboardInterrupt:
            # Shut down
            Log("Execution stopped\n\n", True)
            break

if __name__ == "__main__":
    main()