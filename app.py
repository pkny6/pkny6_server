from flask import Flask, render_template, request, redirect, url_for,flash,session
from flask_sqlalchemy import SQLAlchemy
import datetime
from flask_migrate import Migrate
import os

app = Flask(__name__)

app.secret_key = os.environ.get('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)


class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    time = db.Column(db.DateTime, default=datetime.datetime.now)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    author = db.relationship('User', backref='articles')


@app.route('/')
def index():
    return render_template("index.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        name = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=name).first()
        if name == "" or password == "":
            return render_template("login.html", message="请输入用户名或密码")
        else:
            if user:
                if password == user.password:
                    session['user_id'] = user.id
                    session['username'] = user.username
                    return redirect(url_for("main",username=name))
                else:
                    return render_template("login.html", message="用户密码错误")
            else:
                return redirect(url_for("register", message="不存在，请先注册", username=name))
    else:
        message = request.args.get("message")
        username = request.args.get("username")
        if message:
            return render_template("login.html", message=message, username=username)
        else:
            return render_template("login.html")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        name = request.form.get('username')
        password = request.form.get('password')
        second_password = request.form.get('second_password')
        user = User.query.filter_by(username=name).first()
        if name == "" or password == "" or second_password == "":
            return render_template("register.html", message="请输入用户名或密码或确认密码")
        else:
            if user:
                return render_template("register.html", message="用户名已存在")
            else:
                if password == second_password:
                    user = User(username=name, password=password)
                    db.session.add(user)
                    db.session.commit()
                    return redirect(url_for("login", message="已成功注册，请登录", username=name))
                else:
                    return render_template("register.html", message="两次输入的密码不一致")
    else:
        message = request.args.get("message")
        username = request.args.get("username")
        if message:
            return render_template("register.html", message=message, username=username)
        else:
            return render_template("register.html")


@app.route('/main')
def main():
    username=session.get("username")
    page = request.args.get('page', 1,type=int)
    per_page = 3
    all_articles = Article.query.order_by(Article.time.desc()).all()
    total_pages = (len(all_articles) + per_page - 1) // per_page
    start_index = (page - 1) * per_page
    end_index = start_index + per_page
    articles = all_articles[start_index:end_index]

    return render_template(
        "main.html",
        articles=articles,
        current_page=page,
        total_pages=total_pages,
        username=username
    )

@app.route('/article/<int:article_id>')
def detail(article_id):
    username=session.get("username")
    article = Article.query.get_or_404(article_id)
    return render_template('detail.html', article=article,username=username)


@app.route('/add', methods=['GET', 'POST'])
def add_article():
    if request.method == 'POST':
        title = request.form.get('title')
        article_type = request.form.get('type')
        content = request.form.get('content')
        if not title or not content:
            flash('标题和内容不能为空')
            return render_template('add.html')
        user_id = session.get("user_id")
        # 创建新文章
        new_article = Article(
            title=title,
            type=article_type,
            content=content,
            user_id=user_id
        )

        # 保存到数据库
        db.session.add(new_article)
        db.session.commit()

        # 发布成功后跳转到文章详情页
        return redirect(url_for('detail', article_id=new_article.id))

    # GET请求，显示发布表单
    return render_template('add.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=5000)

