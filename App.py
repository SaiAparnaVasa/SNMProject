from flask import Flask,request,redirect,url_for,render_template,flash,session,send_file
from otp import genotp
from cmail import sendmail
from token_1 import encode,decode
import mysql.connector
from io import BytesIO #Converts bytes format to binary format and vice-versa
from flask_session import Session
import flask_excel as excel
import re
mydb=mysql.connector.connect(host='localhost',user='root',password='admin',db='snmproject') #for connecting database we are using module mysql.connector
app=Flask(__name__) # Creating Object for __name__ class
excel.init_excel(app)
app.config['SESSION_TYPE']='filesystem'
Session(app)
app.secret_key='Aparna@2002'
@app.route('/')
def home():
    return render_template('Welcome.html')
@app.route('/create',methods=['GET','POST'])
def create():
    if request.method=='POST':
        print(request.form)
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        confirm_password=request.form['confirm_password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from users where useremail=%s',[email])
        var1=cursor.fetchone() #brings front-end data to backend fetchall(all record in list of tuple)[(),(),()] fetchone(first record in tuple) (), fetc
        print(var1)
        if var1[0]==0:
            gotp=genotp()
            userdata={'username':username,'useremail':email,'password':password,'otp':gotp}
            subject='OTP for Simple Notes App'
            body=f'Verify email by using the OTP {gotp}'
            sendmail(to=email,subject=subject,body=body)
            flash('OTP has sent to your Email')
            return redirect(url_for('otp',gotp=encode(data=userdata)))
        elif var1[0]>0:
            flash('Email Already Exists')
            return redirect(url_for('Login'))
    return render_template('Create.html')
@app.route('/otp/<gotp>',methods=['GET','POST'])
def otp(gotp):
    if request.method=='POST':
        uotp=request.form['otp']
        try:
            dotp=decode(gotp)
        except Exception as e:
            print(e)
            return 'Something went wrong!!!!'
        else:
            if uotp==dotp['otp']:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('insert into users(username,useremail,password) values(%s,%s,%s)',[dotp['username'],dotp['useremail'],dotp['password']])
                mydb.commit()
                cursor.close()
                return redirect(url_for('Login'))
            else:
                flash('OTP wrong')
                return redirect(url_for('Create'))
    return render_template('otp.html')
@app.route('/Login',methods=['GET','POST'])
def Login():
    if not session.get('user'):
        if request.method=='POST':
            usermail=request.form['email']
            password=request.form['password']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(useremail) from users where useremail=%s',[usermail])
            bdata=cursor.fetchone()
            if bdata[0]==1:
                cursor.execute('select password from users where useremail=%s',[usermail])
                bpassword=cursor.fetchone()
                if password==bpassword[0].decode('utf-8'):
                    print(session)
                    session['user']=usermail
                    print(session)
                    return redirect(url_for('Dashboard'))
                else:
                    flash('Password was wrong')
                    return redirect(url_for('Login'))
            else:
                flash('Email not registered please register')
                return redirect(url_for('create'))
        return render_template('Login.html')
    else:
        return redirect(url_for('Dashboard'))
@app.route('/Dashboard')
def Dashboard():
    if session.get('user'):
        return render_template('Dashboard.html')
    else:
        return redirect(url_for('Login'))
@app.route('/Add_Notes',methods=['GET','POST'])
def Add_Notes():
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            if uid:
                try:
                    cursor.execute('insert into notes(title,description,userid) values(%s,%s,%s)',[title,description,uid[0]])
                    mydb.commit()
                    cursor.close()
                except Exception as e:
                    print(e)
                    flash('Duplicate title entry')
                    return redirect(url_for('Dashboard'))
                else:
                    flash('Notes added successfully')
                    return redirect(url_for('Dashboard'))
            else:
                return 'Something went wrong to fetch uid'
        return render_template('Add_Notes.html')
    else:
        return redirect(url_for('Login'))
@app.route('/View_all_Notes')
def View_all_Notes():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select nid,title,created_at from notes where userid=%s',[uid[0]])
            notesdata=cursor.fetchall()
            cursor.close()
        except Exception as e:
            print(e)
            flash('No data found')
            return redirect(url_for('Dashboard'))
        else:
            return render_template('View_all_Notes.html',notesdata=notesdata)
    else:
        return redirect(url_for('Login'))
@app.route('/View/<nid>')
def View(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select * from notes where nid=%s',[nid])
            notesdata=cursor.fetchone() #(1,'Python','High-level Language','2024-12-14 21:52:28',4)
        except Exception as e:
            print(e)
            flash('Notes not found')
            return redirect(url_for('Dashboard'))
        else:
            return render_template('View.html',notesdata=notesdata)
    else:
        return redirect(url_for('Login'))
@app.route('/Update/<nid>',methods=['GET','POST'])
def Update(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select * from notes where nid=%s',[nid])
        notesdata=cursor.fetchone()
        if request.method=='POST':
            title=request.form['title']
            description=request.form['description']
            cursor.execute('update notes set title=%s, description=%s where nid=%s',[title,description,nid])
            mydb.commit()
            flash('Notes updated Successfully')
            return redirect(url_for('View',nid=nid))
        return render_template('Update.html',notesdata=notesdata)
    else:
        return redirect(url_for('Login'))
@app.route('/Delete/<nid>')
def Delete(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('delete from notes where nid=%s',[nid])
            mydb.commit()
        except Exception as e:
            print(e)
            flash('Notes not found')
            return redirect(url_for('Dashboard'))
        else:
            flash('Notes Deleted Successfully')
            return redirect(url_for('View_all_Notes'))
    else:
        return redirect(url_for('Login'))
@app.route('/Upload_files',methods=['GET','POST'])
def Upload_files():
    if session.get('user'):
        try:
            if request.method=='POST':
                filedata=request.files['choose_me']
                print(filedata)
                fdata=filedata.read()
                filename=filedata.filename
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select userid from users where useremail=%s',[session.get('user')])
                uid=cursor.fetchone()
                cursor.execute('insert into file_data(filename,fdata,added_by) values(%s,%s,%s)',[filename,fdata,uid[0]])
                mydb.commit()
                cursor.close()
                flash('File uploaded Successfully')
                return redirect(url_for('Dashboard'))
        except Exception as e:
            print(e)
            flash('Unable to upload file')
            return redirect(url_for('Dashboard'))
        else:
            return render_template('Upload_files.html')
    else:
        return redirect(url_for('Login'))
@app.route('/View_all_Files')
def View_all_Files():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select fid,filename,created_at from file_data where added_by=%s',[uid[0]])
            filesdata=cursor.fetchall()
        except Exception as e:
            print(e)
            flash('Files not found')
            return redirect(url_for('Dashboard'))
        else:
            return render_template('View_all_Files.html',filesdata=filesdata)
    else:
        return redirect(url_for('Login'))
@app.route('/View_files/<fid>')
def View_files(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select filename,fdata from file_data where fid=%s',[fid])
            filedata=cursor.fetchone()
            bytes_data=BytesIO(filedata[1])
            return send_file(bytes_data,download_name=filedata[0],as_attachment=False)  #send_file loads the file
        except Exception as e:
            print(e)
            flash("Couldn't load file")
            return redirect(url_for('Dashboard'))
    else:
        return redirect(url_for('Login'))
@app.route('/Download/<fid>')
def Download(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select filename,fdata from file_data where fid=%s',[fid])
            filedata=cursor.fetchone()
            bytes_data=BytesIO(filedata[1])
            return send_file(bytes_data,download_name=filedata[0],as_attachment=True)
        except Exception as e:
            print(e)
            flash("Couldn't download file")
            return redirect(url_for('Dashboard'))
    else:
        return redirect(url_for('Login'))
@app.route('/Delete_file/<fid>')
def Delete_file(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('delete from file_data where fid=%s',[fid])
            mydb.commit()
        except Exception as e:
            print(e)
            flash('File not found')
            return redirect(url_for('Dashboard'))
        else:
            flash('File deleted Successfully')
            return redirect(url_for('View_all_Files'))
    else:
        return redirect(url_for('Login'))
@app.route('/Logout')
def Logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('Login'))
    else:
        return redirect(url_for('Login'))
@app.route('/Get_Excel_Data')
def Get_Excel_Data():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select userid from users where useremail=%s',[session.get('user')])
            uid=cursor.fetchone()
            cursor.execute('select nid,title,description,created_at from notes where userid=%s',[uid[0]])
            notesdata=cursor.fetchall()
            cursor.close()
        except Exception as e:
            print(e)
            flash('No data found')
            return redirect(url_for('Dashboard'))
        else:
            array_data=[list(i) for i in notesdata]
            columns=['Notesid','Title','Description','Created_at']
            array_data.insert(0,columns)
            return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')
    else:
        return redirect(url_for('Login'))
@app.route('/Search',methods=['GET','POST'])
def Search():
    if session.get('user'):
        if request.method=='POST':
            search=request.form['searcheddata']
            strg=['A-Za-z0-9']
            pattern=re.compile(f'^{strg}',re.IGNORECASE)
            if (pattern.match(search)):
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select * from notes where nid like %s or title like %s or description like %s or created_at like %s',[search+'%',search+'%',search+'%',search+'%'])
                sdata=cursor.fetchall()
                cursor.close()
                return render_template('Dashboard.html',sdata=sdata)
            else:
                flash('No data found')
                return redirect(url_for('Dashboard'))
        else:
            return render_template('Dashboard.html')
    else:
        return redirect(url_for('Login'))
app.run(use_reloader=True,debug=True)