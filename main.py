from datetime import datetime
import json
from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re

app = Flask(__name__)

app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'user'
app.config['MYSQL_PASSWORD'] = 'Password123#@!'
app.config['MYSQL_DB'] = 'document_control'

mysql = MySQL(app)


@app.route('/pythonlogin/login/', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password,))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('index.html', msg=msg)


@app.route('/pythonlogin/logout/')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/pythonlogin/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        is_admin = True

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s, %s)', (username, password, email, is_admin))
            mysql.connection.commit()
            msg = 'You have successfully registered!'
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
    return render_template('register.html', msg=msg)


@app.route('/login/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))


@app.route('/pythonlogin/profile')
def profile():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        return render_template('profile.html', account=account)
    return redirect(url_for('login'))


@app.route('/pythonlogin/customer', methods=['GET', 'POST', 'DELETE', 'UPDATE'])
def customer():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        if account['is_admin']:
            msg = ''
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
                username = request.form['username']
                password = request.form['password']
                email = request.form['email']
                is_admin = False

                cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
                account = cursor.fetchone()
                if account:
                    msg = 'Account already exists!'
                elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
                    msg = 'Invalid email address!'
                elif not re.match(r'[A-Za-z0-9]+', username):
                    msg = 'Username must contain only characters and numbers!'
                elif not username or not password or not email:
                    msg = 'Please fill out the form!'
                else:
                    if 'id' in request.form:
                        cursor.execute("""
                            UPDATE users SET username=%s, password=%s, email=%s, is_admin=%s WHERE id=%s
                        """, (username, password, email, is_admin, request.form['id']))
                        mysql.connection.commit()
                        cursor.execute('SELECT * FROM users WHERE is_admin = %s', (False,))
                        accounts = cursor
                        return render_template('customers.html', accounts=accounts)
                    cursor.execute('INSERT INTO users VALUES (NULL, %s, %s, %s, %s)', (username, password, email, is_admin))
                    mysql.connection.commit()
                    msg = 'You have created customer!'
                cursor.execute('SELECT * FROM users WHERE is_admin = %s', (False,))
                accounts = cursor
                return render_template('customers.html', accounts=accounts)
            elif request.method == 'POST':
                return render_template('create_customer.html')
            elif request.method == 'GET':
                if request.args.get('_method') == 'EDIT' and request.args.get('id', None):
                    cursor.execute('SELECT * FROM users WHERE id = %s', (request.args.get('id')))
                    account = cursor.fetchone()
                    return render_template('edit_customer.html', account=account)

                if request.args.get('_method') == 'DELETE' and request.args.get('id', None):
                    cursor.execute('DELETE FROM users WHERE id = %s', (request.args.get('id'),))
                    mysql.connection.commit()
                cursor.execute('SELECT * FROM users WHERE is_admin = %s', (False,))
                accounts = cursor
                return render_template('customers.html', accounts=accounts)
        else:
            msg = 'You do not have permissions.'
            return render_template('index.html', msg=msg)
    return redirect(url_for('login'))


def myconverter(o):
    if isinstance(o, datetime):
        return o.__str__()


@app.route('/pythonlogin/documents', methods=['GET', 'POST'])
def document():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
        account = cursor.fetchone()

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        if request.method == 'POST' and 'name' in request.form and 'document_type' in request.form and 'text' in request.form:
            name = request.form['name']
            document_type = request.form['document_type']
            text = request.form['text']
            external_file = request.form.get('external_file', '')
            created = datetime.now()
            if account['is_admin']:
                cursor.execute('INSERT INTO documents VALUES (NULL, %s, %s, %s, %s)', (name, created, external_file, document_type))
                document_id = cursor.lastrowid
                mysql.connection.commit()

                cursor.execute('INSERT INTO draft VALUES (NULL, %s, %s, %s)', (text, created, account['id']))
                draft_id = cursor.lastrowid
                mysql.connection.commit()

                cursor.execute('INSERT INTO document_draft VALUES (NULL, %s, %s, %s, %s)', (document_id, draft_id, account['id'], created))
                mysql.connection.commit()

                cursor.execute('SELECT * FROM documents')
            else:
                return "Error"
            document = cursor.fetchall()
            return json.dumps(document, default=myconverter)
        elif request.method == 'POST':
            return render_template('create_document.html')
        elif request.method == 'GET':
            if request.args.get('_method') == 'GET' and request.args.get('id', None):
                if account['is_admin']:
                    cursor.execute('SELECT * FROM documents WHERE id = %s', (request.args.get('id'),))
                    documents = cursor.fetchone()
                else:
                    cursor.execute('SELECT * FROM documents WHERE id = %s, user_id= %s', (request.args.get('id'), session['id']))
                    documents = cursor.fetchone()
            else:
                if account['is_admin']:
                    cursor.execute('SELECT * FROM documents')
                    documents = cursor.fetchall()
                else:
                    cursor.execute('SELECT document_id FROM customer_document WHERE user_id = %s', (session['id'],))
                    documents_ids = cursor.fetchall()
                    documents_id_list = []
                    for documents_id in documents_ids:
                        documents_id_list.append(documents_id['document_id'])

                    cursor.execute('SELECT * FROM documents WHERE id IN %s', (documents_id_list,))
                    documents = cursor.fetchall()
            if documents:
                return json.dumps(documents, default=myconverter)
            else:
                return 'No document'
    return redirect(url_for('login'))


@app.route('/pythonlogin/draft', methods=['GET', 'POST'])
def draft():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
        account = cursor.fetchone()

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if request.method == 'POST' and 'document_id' in request.form and 'text' in request.form:
            text = request.form['text']
            document_id = request.form['document_id']
            created = datetime.now()

            if not account['is_admin']:
                cursor.execute('SELECT document_id FROM customer_document WHERE user_id = %s', (account['id'],))
                document_ids = cursor.fetchall()
                document_id_list = []
                for document_id in document_ids:
                    document_id_list.append(document_id['document_id'])

                if not int(request.args.get('document_id')) in document_id_list:
                    return 'Error'

            cursor.execute('INSERT INTO draft VALUES (NULL, %s, %s, %s)', (text, created, account['id']))
            draft_id = cursor.lastrowid
            mysql.connection.commit()

            cursor.execute('INSERT INTO document_draft VALUES (NULL, %s, %s, %s, %s)', (document_id, draft_id, account['id'], created))
            mysql.connection.commit()
            return 'Draft Created successfully'

        drafts = None
        if request.method == 'GET':
            if request.args.get('_method') == 'GET' and request.args.get('id', None):
                if account['is_admin']:
                    cursor.execute('SELECT * FROM drafts WHERE id = %s', (request.args.get('id'),))
                    drafts = cursor.fetchone()
                else:
                    cursor.execute('SELECT * FROM drafts WHERE id = %s, user_id = %s', (request.args.get('id'), account['id']))
                    drafts = cursor.fetchone()
            else:
                if account['is_admin']:
                    cursor.execute('SELECT * FROM drafts WHERE')
                    drafts = cursor.fetchone()
                else:
                    cursor.execute('SELECT * FROM drafts WHERE user_id = %s', (account['id'],))
                    drafts = cursor.fetchone()
        return json.dumps(drafts, default=myconverter)
    return redirect(url_for('login'))


@app.route('/pythonlogin/customer_document', methods=['POST'])
def customer_document():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
        account = cursor.fetchone()

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        if account['is_admin']:
            if request.method == 'POST' and 'document_id' in request.form and 'user_id' in request.form:
                user_id = request.form['user_id']
                document_id = request.form['document_id']

                cursor.execute('INSERT INTO customer_document VALUES (NULL, %s, %s, )', (document_id, user_id))
                mysql.connection.commit()
                return 'Document circulated successfully'
        return 'Error'
    return redirect(url_for('login'))


@app.route('/pythonlogin/document_drafts', methods=['GET'])
def document_draft():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
        account = cursor.fetchone()

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        drafts = None
        if request.method == 'GET':
            if request.args.get('_method') == 'GET' and request.args.get('document_id', None):
                if account['is_admin']:
                    cursor.execute('SELECT draft_id FROM document_draft WHERE document_id = %s', (request.args.get('document_id'),))
                    draft_ids = cursor.fetchall()
                    draft_id_list = []
                    for draft_id in draft_ids:
                        draft_id_list.append(draft_id['draft_id'])
                    cursor.execute('SELECT * FROM drafts WHERE draft_id IN %s', (draft_id_list,))

                    drafts = cursor.fetchall()
                else:
                    cursor.execute('SELECT document_id FROM customer_document WHERE user_id = %s', (account['id'],))
                    document_ids = cursor.fetchall()
                    document_id_list = []
                    for document_id in document_ids:
                        document_id_list.append(document_id['document_id'])
                    try:
                        if int(request.args.get('document_id')) in document_id_list:
                            cursor.execute('SELECT draft_id FROM document_draft WHERE document_id = %s', (request.args.get('document_id'),))
                            draft_ids = cursor.fetchall()
                            draft_id_list = []
                            for draft_id in draft_ids:
                                draft_id_list.append(draft_id['draft_id'])
                            cursor.execute('SELECT * FROM drafts WHERE id IN %s ORDER BY created', (draft_id_list,))

                            drafts = cursor.fetchall()
                            return json.dumps(drafts, default=myconverter)
                        else:
                            return 'Error'
                    except TypeError:
                        return "Error"
        return json.dumps(drafts, default=myconverter)
    return redirect(url_for('login'))
