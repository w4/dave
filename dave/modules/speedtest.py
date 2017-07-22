from requests import get
from bs4 import BeautifulSoup
import dave.module
from twisted.words.protocols.irc import assembleFormattedText, attributes as A

@dave.module.match(r'https?://(?:www\.|beta\.)?speedtest\.net/(?:my-)?result/([0-9]+)')
@dave.module.priority(dave.module.Priority.HIGHEST)
@dave.module.dont_always_run_if_run()
def speedtest(bot, args, sender, source):
    res = get("http://www.speedtest.net/result/{}".format(args[0]), timeout=3)

    soup = BeautifulSoup(res.text, "html.parser")
    download = soup.select(".share-speed.share-download p")[0].text
    upload = soup.select(".share-speed.share-upload p")[0].text
    ping = soup.select(".share-data.share-ping p")[0].text
    isp = soup.select(".share-data.share-isp p")[0].text

    bot.msg(source, assembleFormattedText(A.normal[
        A.bold["{}: ".format(isp)],
        "Download: ", A.bold[str(download)], " ",
        "Upload: ", A.bold[str(upload)], " ",
        "Ping: ", A.bold[str(ping)]
    ]))