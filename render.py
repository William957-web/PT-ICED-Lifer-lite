from flask import *
from hashlib import md5
import sqlite3
import os
from flaskext.markdown import Markdown

app = Flask(__name__)
app.secret_key = os.urandom(16)
Markdown(app, extensions=['tables'])

# 数据库配置
DATABASE = 'blog.db'

# 创建数据库连接
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

# 关闭数据库连接
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

# 创建表格
def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.route('/')
def index():
    db=get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM comment ORDER BY id DESC")
    comments = cur.fetchall()
    db.close()
    return render_template('index.html', comments=comments)



# 用户登录
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = md5(request.form['password'].encode()).hexdigest()
        db = get_db()
        cur = db.execute('SELECT * FROM users WHERE username=? AND password=?', (username, password))
        user = cur.fetchone()
        if user:
            session['logged_in'] = True
            session['username'] = username
            return redirect('/')
        else:
            return render_template('login.html', error='Invalid username or password.')
    return render_template('login.html')

# 用户注销
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = md5(request.form['password'].encode()).hexdigest()
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password,))
        db.commit()
        db.close()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/add_comment', methods=['POST'])
def add_comment():
    if 'username' in session:
        user = session['username']
        content = request.form['content']
        db = get_db()
        cur = db.cursor()
        cur.execute("INSERT INTO comment (user, content) VALUES (?, ?)", (user, content))
        db.commit()
        db.close()
        return redirect('/')
    else:
        return redirect(url_for('login'))

@app.route('/backup', methods=['GET', 'POST'])
def enter_pin():
    if request.method == 'POST':
        pin = request.form['pin']
        # 檢查輸入的 PIN 碼是否符合要求
        if pin=='2694':
            session['isadmin']=True
            return redirect(url_for('success'))
        else:
            error = 'Invalid PIN. Please enter a 4-digit number.'
            return render_template('pin.html', error=error)
    return render_template('pin.html')

@app.route('/success')
def success():
    if session['isadmin']!=True:
        error = 'Enter the pincode first'
        return render_template('pin.html', error=error)
    else:
        return render_template('success.html')

@app.route('/download_backup')
def download_backup():
    backup_file_path = 'backup.db'
    return send_file(backup_file_path, as_attachment=True)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=80)
