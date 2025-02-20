import boto3
# from environs import Env
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

# env = Env()
# env.read_env()
S3_ACCESS_KEY_ID=os.getenv('AWS_ACCESS')
S3_SECRET_KEY=os.getenv('AWS_SECRET')

class SesWrapper:
    def __init__(self):
        self.ses_client = boto3.client(
            'ses', 
            aws_access_key_id=S3_ACCESS_KEY_ID,
            aws_secret_access_key=S3_SECRET_KEY,
            region_name="ap-south-1"
        )

    def send_email(self, receiver_email_address='', receiver_email_address_arr=[], subject='', html_body='', sender_email_address='shreya@medicolifepartner.com', is_bulk=False):
        try:
            if is_bulk==True: print("sending bulk emails")

            message = {
                "Body": {
                    "Html": {
                        "Charset": "UTF-8",
                        "Data": html_body
                    }
                },
                "Subject": {
                    "Charset": 'UTF-8',
                    "Data": subject
                }
            }

            self.ses_client.send_email(
                Destination={
                    "ToAddresses": [receiver_email_address] if not is_bulk else receiver_email_address_arr
                },
                Message=message,
                Source=sender_email_address,
                ReplyToAddresses=[sender_email_address]
            )

            return True
        except Exception as err:
            print("Error while sending email >> ", str(err))
            return False

    def send_email_with_attachment(self, receiver_email_address='', subject='', text_body='', sender_email_address='noreply@peekup.app', attachment=None):
        try:
            # Create a MIME message with the email body and attachment
            msg = MIMEMultipart()
            msg['Subject'] = subject
            msg['From'] = sender_email_address
            msg['To'] = receiver_email_address

            body = MIMEText(text_body, 'plain')
            msg.attach(body)

            if attachment:
                part = MIMEApplication(attachment['data'], _subtype="csv")
                part.add_header('Content-Disposition', f'attachment; filename="{attachment["file_name"]}"')
                msg.attach(part)

            raw_message = msg.as_string()

            self.ses_client.send_raw_email(
                RawMessage={'Data': raw_message}
            )

            return True

        except Exception as err:
            print("Error while sending email >> ", str(err))
            return False