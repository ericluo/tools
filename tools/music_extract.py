import os
import logging
import shutil

rootdir = "E:\BaiduNetdiskDownload\JYCD集合"
destdir = "E:\BaiduNetdiskDownload\JY"
basenames = [name for name in os.listdir(rootdir) if os.path.isdir(os.path.join(rootdir, name))]

logging.basicConfig(level=logging.INFO)

if not os.path.exists(destdir):
    os.mkdir(destdir)
for basename in basenames:
    source = os.path.join(rootdir, basename, "Track04.mp3")
    dest   = os.path.join(destdir, "{}.mp3".format(basename))

    try:
        logging.info("copy {} to {}".format(source, dest))
        shutil.copy2(source, dest)
    except Exception as e:
        logging.error("Couldn't find file: %r", source)
        
