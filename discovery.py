import os, slackclient

MAXPLS_SLACK_NAME = os.environ.get('MAXPLS_SLACK_NAME')
VERIFICATION_TOKEN = os.environ.get('VERIFICATION_TOKEN')
OAUTH_TOKEN = os.environ.get('OAUTH_TOKEN_SLACK')

#initialize slack client
slack_client = slackclient.SlackClient(OAUTH_TOKEN)

#check if everything is alright
print(MAXPLS_SLACK_NAME)
print(OAUTH_TOKEN)

is_ok = slack_client.api_call("users.list").get('ok')
print(is_ok)

#find the id of our slack bot
if(is_ok):
    for user in slack_client.api_call("users.list").get("members"):
        if user.get('name') == MAXPLS_SLACK_NAME:
            print(user.get('id'))
