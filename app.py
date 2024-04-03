# from flask import Flask,url_for,redirect,render_template,request,flash
# from flask_mysqldb import MySQL
from flask import Flask,redirect,url_for,render_template,request,flash,abort,session,send_file
from flask_session import Session
from key import secret_key,salt1,salt2
from itsdangerous import URLSafeTimedSerializer
from stoken import token
import os
from flask_mysqldb import MySQL
from mail import sendmail
from io import BytesIO
app=Flask(__name__)
app.secret_key = secret_key
app.config['SESSION_TYPE'] = 'filesystem'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Bittu123'
app.config['MYSQL_DB'] = 'hotel'
mysql = MySQL(app)
@app.route('/home',methods=['GET','POST'])
def home():
     return render_template('home.html')
@app.route('/',methods=['GET','POST'])
def index():
     return render_template('index.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        username = request.form['username']
        email = request.form['email']
        password= request.form['password']
        phno= request.form['phno']
        state=request.form['state']
        address=request.form['address']
        pincode=request.form['pincode']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from user where username=%s',[username])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from user where email=%s',[email])
        count1=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            flash('username already in use')
            return render_template('usersignin.html')
        elif count1==1:
            flash('Email already in use')
            return render_template('usersignin.html')
        data={'username':username,'email':email,'password':password,'phno':phno,'state':state,'address':address,'pincode':pincode}
        subject='Email Confirmation'
        body=f"Thanks for signing up\n\nfollow this link for further steps-{url_for('confirm',token=token(data,salt1),_external=True)}"
        sendmail(to=email,subject=subject,body=body)
        flash('Confirmation link sent to mail')
        return redirect(url_for('login'))
    return render_template('usersignin.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        print(request.form)
        username=request.form['username']
        password=request.form['password']
        cursor=mysql.connection.cursor()
        cursor.execute('SELECT count(*) from user where username=%s and password=%s',[username,password])
        count=cursor.fetchone()[0]
        if count==1:
            session['user']=username
            return redirect(url_for('home'))
            
        else:
            flash('Invalid username or password')
            return render_template('userlogin.html')
    return render_template('userlogin.html')

@app.route('/confirm/<token>')
def confirm(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        data=serializer.loads(token,salt=salt1,max_age=180)
    except Exception as e:
        abort (404,'Link Expired register again')
    else:
        cursor=mysql.connection.cursor()
        email=data['email']
        cursor.execute('select count(*) from user where email=%s',[email])
        count=cursor.fetchone()[0]
        if count==1:
            cursor.close()
            flash('You are already registerterd!')
            return redirect(url_for('login'))
        else:
            cursor.execute('insert into user values(%s,%s,%s,%s,%s,%s,%s)',[data['username'],data['email'],data['password'],data['phno'],data['state'],data['address'],data['pincode']])
            mysql.connection.commit()
            cursor.close()
            flash('Details registered!')
            return redirect(url_for('login'))


@app.route('/aforget',methods=['GET','POST'])
def aforgot():
    if request.method=='POST':
        id1=request.form['name']
        cursor=mysql.connection.cursor()
        cursor.execute('select count(*) from user where username=%s',[id1])
        count=cursor.fetchone()[0]
        cursor.close()
        if count==1:
            cursor=mysql.connection.cursor()

            cursor.execute('SELECT email  from user where username=%s',[id1])
            email=cursor.fetchone()[0]
            cursor.close()
            subject='Forget Password'
            confirm_link=url_for('areset',token=token(id1,salt=salt2),_external=True)
            body=f"Use this link to reset your password-\n\n{confirm_link}"
            sendmail(to=email,body=body,subject=subject)
            flash('Reset link sent check your email')
            return redirect(url_for('login'))
        else:
            flash('Invalid email id')
            return render_template('forgot.html')
    return render_template('forgot.html')


@app.route('/areset/<token>',methods=['GET','POST'])
def areset(token):
    try:
        serializer=URLSafeTimedSerializer(secret_key)
        id1=serializer.loads(token,salt=salt2,max_age=180)
    except:
        abort(404,'Link Expired')
    else:
        if request.method=='POST':
            newpassword=request.form['npassword']
            confirmpassword=request.form['cpassword']
            if newpassword==confirmpassword:
                cursor=mysql.connection.cursor()
                cursor.execute('update user set password=%s where username=%s',[newpassword,id1])
                mysql.connection.commit()
                flash('Reset Successful')
                return redirect(url_for('login'))
            else:
                flash('Passwords mismatched')
                return render_template('newpassword.html')
        return render_template('newpassword.html')
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('home'))
    else:
        flash("already logged out")
        return redirect(url_for('login'))
@app.route('/rooms')
def rooms():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from rooms')
        data=cursor.fetchall()
        return render_template('rooms.html',data=data)
    else:
        return redirect(url_for('login'))
@app.route('/booking',methods=['GET','POST'])
def booking():
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('select * from rooms')
        data=cursor.fetchall()
        if request.method=="POST":
            rid=request.form['rid']
            customername=request.form['customername']
            phno=request.form['phno']
            cursor=mysql.connection.cursor()
            cursor.execute('update rooms set availability="no" where rid=%s',[rid])
            cursor.execute('insert into booking (rid,customername,phno)values(%s,%s,%s)',[rid,customername,phno])
            mysql.connection.commit()
            cursor.close()
    return render_template('bookings.html',data=data)
@app.route('/checkout/<rid>',methods=['GET','POST'])
def checkout(rid):
    if session.get('user'):
        cursor=mysql.connection.cursor()
        cursor.execute('update rooms set availability="yes" where rid=%s',[rid])
        mysql.connection.commit()
        cursor.close()
    return redirect(url_for('rooms'))
app.run(debug=True,use_reloader=True)
