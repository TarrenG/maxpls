import os, slackclient, time, random, boxer, re
#delay in seconds before checking for new events
SOCKET_DELAY = 1

#slack enviroment variables
#MAXPLS_SLACK_ID='U7PJXM4UD'
MAXPLS_SLACK_NAME = os.environ.get('MAXPLS_SLACK_NAME')
OAUTH_TOKEN_SLACK = os.environ.get('OAUTH_TOKEN_SLACK')
MAXPLS_SLACK_ID = os.environ.get('MAXPLS_SLACK_ID')
MESSAGE_SIZE_LIMIT = 40

slack_client = slackclient.SlackClient(OAUTH_TOKEN_SLACK)


print("--------{}---------".format(MAXPLS_SLACK_ID))

# how the bot is mentioned on slack
def get_mention(user):
    return '<@{user}>'.format(user=user)

maxpls_slack_mention = get_mention(MAXPLS_SLACK_ID)
name_pattern = re.compile("\[\[(.*?)\]\]")
resume_pattern = re.compile("resume\[(.*?)\]")

def is_for_me(event):
    """ determine if message @mentions me or is a DM """
    event_type = event.get('type')
    print("message is:",event.get('text'))
    print(maxpls_slack_mention, 'is maxpls_slack_mention')
    #print("\n\n",name_pattern.search(str(event.get('text'))) is not None )
    if event_type and event_type == 'message' and not event.get('user')==MAXPLS_SLACK_ID:
        text = event.get('text')
        channel = event.get('channel')
        #print(text.strip().split(),": is text.strip().split()")
        if name_pattern.search(str(event.get('text'))) is not None:
            print("\n\n %s \n\n" % name_pattern.search(str(event.get('text'))).group(0))
            return True
        if resume_pattern.search(str(event.get('text'))) is not None:
            print("\n\n %s \n\n" % resume_pattern.search(str(event.get('text'))).group(0))
            return True
        if (is_private(event)):
            return True
        if text is not None  and maxpls_slack_mention in text.strip().split():
            return True

    return False

""" HELPER  """

def is_private(event):
    """ check if event is a Direct Message """
    return event.get('channel').startswith('D')

def handle_message(message, user, channel, timestamp):
    print("\n\nhandling message: %s" % message)
    if is_hi(message):
        user_mention = get_mention(user)
        print(channel)
        post_message(message=say_hi(user_mention),channel=channel)
    elif is_bye(message):
        user_mention = get_mention(user)
        post_message(message=say_bye(user_mention), channel=channel)
    elif is_help_request(message):
        user_mention = get_mention(user)
        print("TIMESTAMP IS ",timestamp)
        slack_client.api_call("reactions.add", channel=channel, name="white_check_mark", timestamp=timestamp, as_user=True)
        post_message(message=say_user_guide(user_mention),channel=user)
    elif is_boxer_request(message):
        user_mention = get_mention(user)
        query = name_pattern.search(message).group(0)[2:-2].strip()
        has_flags = "|" in query
        name = query.split("|")[0]
        flags = []
        if (has_flags):
            flags = " ".join((query.split("|")[1:])[0].split(" "))
        print("name: %s\nflags: %s\ntype: %s" % (name, flags, type(flags)))
        print ('name' in flags)
        print("is_boxer_request: %s " % message)
        post_message(message=say_boxer_info(user_mention,name, flags), channel=channel)
    elif is_boxer_resume_request(message):
        user_mention = get_mention(user)
        name = resume_pattern.search(message).group(0)[7:-1].strip()
        print("\n is boxer resume request: name is %s" % name)
        message = say_boxer_resume(user_mention, name)
        if (len(message.split("\n")) <= 40 ):
            post_message(message=message, channel=channel)
        else:
            #post_message(message="%s Whew! that's a long one, check your dm's so I don't clog the chat." % user_mention, channel=channel)
            post_message_thread(message=message, channel=channel, ts=timestamp)

def post_message(message, channel):
    """ post a message into the chat as normal """
    slack_client.api_call('chat.postMessage', channel=channel,
        text=message, as_user=True)

def post_message_thread(message, channel, ts):
    """ when messages are too long and will clog chat, start a thread to original message instead """
    slack_client.api_call('chat.postMessage', channel=channel, text=message, as_user=True, thread_ts=ts)


""" DETERMINING MESSAGE INTENTIONS """

def is_help_request(message):
    tokens = [word.lower() for word in message.strip().split()]
    return any(g in tokens
                for g in ['help', 'commands', 'info'])

def is_hi(message):
    tokens = [word.lower() for word in message.strip().split()]
    return any(g in tokens
                for g in ['hello', 'hi', 'hey', 'sup'])

def is_bye(message):
    tokens = [word.lower() for word in message.strip().split()]
    return any(g in tokens
                  for g in ['bye', 'goodbye', 'revoir', 'adios', 'later', 'cya'])

def is_boxer_request(message):
    print("in is boxer request: %s" % message)
    if name_pattern.search(message) is not None:
        return True
    else:
        return False

def is_boxer_resume_request(message):
    print("\n\n\nin boxer resume request %s" % message)
    if resume_pattern.search(message) is not None:
        return True
    else:
        return False

""" MESSAGE RESPONSES """

def say_user_guide(user_mention):
    """ give a short description of commands/use cases """
    commands = "I can lookup basic boxer information just use the formatting [[boxer name]] or [[boxrec id]] and ill see what I can find, you may also use flags by naming the specific info you want ex: [[errol spence|record reach height]] to only return those requested flags! Additionally I can lookup a fighters resume with the command resme[name/id]!"
    return commands

def say_hi(user_mention):
    """ Say hi to a user formatting their mention """
    response_template = random.choice(['sup, {mention}', 'Yo!', "heyo {mention}"])
    return response_template.format(mention=user_mention)

def say_bye(user_mention):
    """ Say goodbye to a user formatting their mention """
    response_template = random.choice(['peace nerd', 'bye, {mention}', 'bye bye'])
    return response_template.format(mention=user_mention)

def say_boxer_info(user_mention, name, flags):
    """ send some information about the boxer """
    boxer_dict = boxer.boxer_lookup(name)
    if(boxer_dict is None):
        print("could not find boxer")
        return "Couldn't find that boxer"
    print(boxer_dict)
    response_template = ""
    for key, value in boxer_dict.items():
        key = key.strip("'")
        print(key, flags, key in flags, len(flags))
        if ((key in flags) or len(flags) == 0): #remove this line to get previous functionality
            response_template = response_template+("%s: %s\n" %(key, value))
    if (response_template == ""):
        return ""
    else:
        return "``` "+str(response_template)+" ```"

def say_boxer_resume(user_mention, name):
    """ send information on boxers resume """
    resume_dict = boxer.boxer_resume(name)
    if (resume_dict is None):
        return "Couldn't find that boxer"
    response_template = ""
    for key, value in resume_dict.items():
        response_template = response_template+("%s - %s\n" % (value, key))
    return "```"+str(response_template)+"```"

""" RUN """

def run():
    if slack_client.rtm_connect():
        print('[.] MaxPls has entered the big drama show...')
        while True:
            event_list = slack_client.rtm_read()
            if len(event_list) > 0:
                for event in event_list:
                    print(event)
                    if is_for_me(event):
                        print("Its for me!!")
                        handle_message(message=event.get('text'),
                            user=event.get('user'), channel=event.get('channel'),timestamp=event.get('ts'))
                        time.sleep(SOCKET_DELAY)
    else:
        print(slack_client.rtm_connect())
        print('[!] Connection to Slack failed.')

if __name__ == '__main__':
    run()
