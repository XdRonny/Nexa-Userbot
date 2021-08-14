# Copyright (c) 2021 Itz-fork
# Part of: Nexa Userbot
# Experimantal Mega.nz Downloader Plugin (Uses megatools)

import os
import subprocess
import shutil

from pyrogram import filters
from pyrogram.types import Message
from functools import partial
from asyncio import get_running_loop
from fsplit.filesplit import Filesplit

from pyrogram_ub import NEXAUB, CMD_HELP
from pyrogram_ub.helpers.up_to_tg import guess_and_send
from config import Config

CMD_HELP.update(
    {
        "megatools": """
**Megatools,**

  ✘ `megadl` - To Download Files / Folder from Mega.nz
"""
    }
)

# Download path
megadir = "./NexaUb/Megatools"

# Run bash cmd in python
def nexa_mega_runner(command):
    run = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    shell_ouput = run.stdout.read()[:-1].decode("utf-8")
    return shell_ouput

# Splitting large files
def split_files(input_file, out_base_path):
    nexa_fs = Filesplit()
    split_file = input_file
    split_fsize = 2040108421
    out_path = out_base_path
    nexa_fs.split(file=split_file, split_size=split_fsize, output_dir=out_path)

@NEXAUB.on_message(filters.me & filters.command("megadl", Config.CMD_PREFIX))
async def megatoolsdl(_, message: Message):
    megatools_msg = await message.edit("`Processing...`")
    url = message.text
    cli_user_id = str(message.from_user.id)
    cli_download_path = megadir + "/" + cli_user_id
    if len(message.command) < 2:
        await megatools_msg.edit("`Please send a valid mega.nz link to download!`")
        return
    # Mega url to download
    cli_url = url.split(None, 1)[1]
    # Checking if sent message has a vaild mega.nz url
    if "https://mega.nz/" not in url:
        await megatools_msg.edit("`Please send a valid mega.nz link to download!`")
        return
    # Checking if there is a ongoing task for the user
    if os.path.isdir(cli_download_path):
        await megatools_msg.edit("`Already One Process is Going On. Please wait until it's finished!`")
        return
    else:
        os.makedirs(cli_download_path)
    await message.reply(f"`Starting to download file / folder from mega.nz!` \n\nThis may take sometime. Depends on your file / folder size.")
    megacmd = f"megatools dl --limit-speed 0 --path {cli_download_path} {cli_url}"
    loop = get_running_loop()
    await loop.run_in_executor(None, partial(nexa_mega_runner, megacmd))
    await megatools_msg.edit("`Downloading Finished! Trying to upload now`")
    try:
        folder_f = [f for f in os.listdir(cli_download_path) if os.path.isfile(os.path.join(cli_download_path, f))]
        for nexa_m in folder_f:
            file_size = os.stat(cli_download_path+"/"+nexa_m).st_size
            if file_size > 2040108421:
                split_out_dir = cli_download_path + "/" + "splitted_files"
                await megatools_msg.edit("`Large File Detected, Trying to split it!`")
                loop = get_running_loop()
                await loop.run_in_executor(None, partial(split_files(input_file=cli_download_path+"/"+nexa_m, out_base_path=split_out_dir)))
                await megatools_msg.edit("`Splitting Finished! Uploading Now...`")
                for splitted_f in split_out_dir:
                    await message.reply_document(splitted_f, caption=f"`Uploaded by` {(await NEXAUB.get_me()).mention}")
                await megatools_msg.edit("`Large Files Splitting and Uploading Finished!`")
            else:
                chat_id = message.chat.id
                await guess_and_send(input_file=cli_download_path+"/"+nexa_m, chat_id=chat_id, thumb_path=cli_download_path)
                await megatools_msg.edit("`Small Files Uploading Finished!`")
    except Exception as e:
        await megatools_msg.edit(f"**Error:** `{e}`")
    try:
        shutil.rmtree(cli_download_path)
    except Exception as e:
        await megatools_msg.edit(f"**Error:** `{e}`")
