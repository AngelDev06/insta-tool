# InstaTool

A basic utility that interacts with the instagram api to retrieve and operate on followers/followings information of a specified user

## Setup

Clone the repository:

```bash
git clone https://github.com/AngelDev06/insta-tool
```

Clone the modified version of the main library:

```bash
git clone https://github.com/AngelDev06/instagrapi
```

Install dependencies:

```bash
cd insta-tool
pip install ../instagrapi
pip install -r requirements.txt
```

Note: it is advised that you use a venv to install the dependencies

Run (in the repository):

```bash
python insta -h
```

## Usage Guide

What you can do with the tool is described in detail when executing the program with `-h` or `--help` flag which prints out the usage help message.
You can also apply these flags to subcommands included (e.g. `python insta log -h`) to provide help for a specific subcommand.

Should be noted that for any command that involves interaction with the instagram API (such as when fetching users), credentials for a bot account should be configured before use.
This can be done via the optional arguments `--name`, `--password` and `--2fa-seed`. The credentials passed via these arguments will be cached for later invocations of the tool without needing to respecify them again.
You can have multiple bot accounts configured (via the args specified) but only one of them will be used each time. You can switch between them by providing only the `--name` argument and the tool will automatically fetch the rest of the credentials.
