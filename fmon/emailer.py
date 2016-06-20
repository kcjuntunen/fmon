import html.parser as HTMLParser
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class TagStripper(HTMLParser.HTMLParser):
    collected_data = ""
    def __init__(self):
        super().__init__(convert_charrefs=True)

    def handle_data(self, data):
        self.collected_data = self.collected_data + data

    def get_collected_data(self):
        return self.collected_data

def send_email(server, sender, passwd, receivers, subj, msg):
    """
    Sends an email. subj, and msg are self-explanatory.
    """
    logger = logging.getLogger('Fmon')
    if (len(sender) > 0 or len(receivers) < 1):
        try:
            message = MIMEMultipart('alternative')
            message['From'] = "do_not_reply@amstore.com"
            message['To']  = ','.join(receivers)
            message['Subject'] = subj
            html = msg
            ts = TagStripper()
            ts.feed(html)
            txt = ts.get_collected_data()
            logger.debug("sending: {0}".format(txt))
            part1 = MIMEText(txt, 'plain')
            part2 = MIMEText(html, 'html')
            message.attach(part1)
            message.attach(part2)
            smtpo = smtplib.SMTP(server)
            smtpo.ehlo()
            smtpo.starttls()
            smtpo.login(sender.split('@', 1)[0], passwd)
            smtpo.sendmail(sender, receivers, message.as_string())
            smtpo.quit()
            return True
        except Exception as e:
            errmsg = "Failure sending email: {0}".format(e.message)
            logger.error(errmsg)
            return False
    else:
        return False
