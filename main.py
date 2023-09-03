from base64 import b64decode
from sys import argv

from instagrapi import Client

client = Client()
username = "angel.tserk"
with open("ps.txt", "rb") as file:
    password = b64decode(file.read()).decode("utf-8")

client.login(username, password)

user_id = client.user_id if len(argv) == 1 else client.user_id_from_username(
    argv[1])

followers_usernames = {
    follower.username
    for follower in client.user_followers(user_id).values()
}
following_usernames = {
    following.username
    for following in client.user_following(user_id).values()
}

for following_username in following_usernames.difference(followers_usernames):
    print(following_username)
