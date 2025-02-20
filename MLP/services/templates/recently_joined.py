# -*- coding: utf-8 -*-

email_conf = '''
<!-- email_template.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        /* Your CSS styles go here */
    </style>
</head>
<body>
    <div id="parent">
        <div id="maindiv">
            <h4>Hi, Below are some of the profiles who have recently registered at medicolifepartner.com. You can search many more profiles through "Simple Search" or "Quick Search" options. Log-on to your <a href="medicolifepartner.com" target="blank">medicolifepartner.com.</a> account, for connecting to many of such profiles.</h4>
            <h3>Recently Joined Profile Details:</h3>
            
            {middle_content_placeholder}

            <h4>Would you like to initiate a conversation with them?</h4>
            <button id="login">SEND MESSAGE</button>
            <hr/>
            <p id="terms"><span>Terms:</span> We at <a href="medicolifepartner.com">medicolifepartner.com</a> do not verify profile details. Verification of the profile of other candidates and any interest to proceed for conversation or marriage with any candidate registered on medicolifepartner.com will be solely candidates & parents' responsibility. Medicolifepartner.com will not take any liability for the authenticity of the details mentioned in any individual’s profiles nor will we be able to provide documentation support in any legal proceedings. If you are not in agreement with the above, please delete your profile and email us within 24 hours at support@medicolifepartner.com</p>
        </div>
        <p>If you no longer want to receive some emails, please adjust your notification settings.</p>
        <p>For any type of support, you can email us at <a href="mailto: akshita@medicolifepartner.com">akshita@medicolifepartner.com</a> or reach us at <a href="tel:+918591912971">+91 8591912971</a>.</p>
        <p>The information contained in this email is confidential and is intended only for the use of the individual named above. If you are not the intended recipient, you are hereby notified that any dissemination, distribution, or copying of this communication is strictly prohibited. If you have received this communication in error, please destroy the message and notify us immediately.</p>
    </div>
</body>
</html>

'''