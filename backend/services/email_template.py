import smtplib
from email.message import EmailMessage
import os

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

def send_verification_email(to_email, name, code):
    msg = EmailMessage()
    msg["Subject"] = "Your SafeOps Verification Code"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    body = f"""
Hello {name},

Thank you for registering with SafeOps. Please use the following verification code to complete your registration:

Verification Code: {code}

This code is valid for 10 minutes. If you did not request this, please ignore this email.

Best regards,
The SafeOps Team
"""
    msg.set_content(body)

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>SafeOps Verification</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f0f4ff;">
  <table width="100%" style="background-color: #1e5fff; padding: 20px 0;">
    <tr>
      <td align="center">
        <h1 style="color: white; margin: 0;">SafeOps</h1>
      </td>
    </tr>
  </table>
  <table align="center" width="100%" style="max-width: 600px; background-color: white; border-radius: 8px; padding: 30px; margin-top: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
    <tr>
      <td align="center">
        <h2 style="color: #1e5fff; margin-bottom: 10px;">Verification Code</h2>
        <p style="color: #333333;">Hello <strong>{name}</strong>,</p>
        <p style="color: #555;">To continue using <strong>SafeOps</strong>, please verify your email address using the code below:</p>
        <div style="font-size: 24px; font-weight: bold; background-color: #e7efff; color: #1e5fff; padding: 15px 30px; border-radius: 10px; display: inline-block; margin: 20px 0;">
          {code}
        </div>
        <p style="color: #777; font-size: 14px;">This code is valid for the next 10 minutes. Do not share it with anyone.</p>
      </td>
    </tr>
  </table>
  <table width="100%" align="center" style="max-width: 600px; padding: 20px; margin-top: 20px; font-size: 12px; color: #aaa; text-align: center;">
    <tr>
      <td>
        © 2025 SafeOps Security Platform. All rights reserved.
      </td>
    </tr>
  </table>
</body>
</html>
"""
    msg.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        print(f" Email sent successfully to {to_email}!")
        return True
    except Exception as e:
        print(f" Failed to send email to {to_email}: {e}")
        return False
