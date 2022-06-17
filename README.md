# Eva 
[![Telegram - Bot](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)](https://t.me/storoxbot)  
Telegram bot that checks users who sent join requests to private groups and channels using captcha.  
Send `/feedback` command to [@storoxbot](https://t.me/storoxbot) to get support.

## Installation  
**Warning: you must have installed at least 3.10 python version!**

1. Clone this repo:  
```git clone https://github.com/utkasoftware/eva-bot && cd eva-bot```
2. Install postgresql and create database for Eva.
3. Go to `cd eva/configs` then rename `mv {example.,}config.ini` config file and fill it in.
4. Run Eva:  
```cd - && python -m eva```  
You may use `screen` or `nohup` to run Eva on VDS.

## Contributing
<details>
<summary>Please read before contributing.</summary>

#### Always test your changes.  
Do not submit something without at least running the module.  

#### Do not make large changes before discussing them first.
We want to know what exactly you are going to make to give you an advice and make sure you are not wasting your time on it.

#### Do not make formatting PRs.  
We know that our code might be not clean enough, but we don't want to merge, view or get notified about 1-line PR which fixes trailing whitelines. Please don't waste everyone's time with pointless changes.

#### We use ```this``` instead of ```self```
Do not ask why, it's too a long story.
</details>
