from flask_mail import Mail, Message

app.config['MAIL_SERVER'] = 'smtp.gmail.com'  
app.config['MAIL_PORT'] = 587  
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'retailsmail.com'  
app.config['MAIL_PASSWORD'] = 'qe gkeq nlee' 
app.config['MAIL_DEFAULT_SENDER'] = 'retailail.com'  

mail = Mail(app)