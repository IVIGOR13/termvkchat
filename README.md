# termvkchat
### Beta version
small program for communication in the social network VKontakte on behalf of the community.

## Important
### Numbering starts at 1, at the end of the message list

## Commands
### In the dialogue selection menu:
* exit - close the programm

### In dialogue
* exit - close the dialog
* del {number} - remove message for your (numbering starts at 1, at the end)
* delfa {number} - remove message for all
* edit {number} {text} - edit message

## Installation
Repository cloning
```
$ git clone https://github.com/IVIGOR13/termvkchat.git
```

## Tuning
```
$ pip install vk_api
$ git clone https://github.com/IVIGOR13/print_chat.git
```
move the file /print_chat/print_chat.py to the directory /termvkchat/

in the settings.txt file, specify the missing data:
* token your vk community
* your name to display in the chat

in the contacts.txt file specify vk_id your contacts

## Launch
```
$ cd termvkchat
$ python termvkchat
```



