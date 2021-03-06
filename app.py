import time

from flask import Flask, render_template, redirect, url_for, flash, request, make_response
from flask.views import MethodView
from flask_bootstrap import Bootstrap
from sqlalchemy.orm import sessionmaker
from flask_cors import *
from werkzeug.utils import escape

from models import engine, User

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.config["SECRET_KEY"] = "123456"
app.config["token"] = "hutacm601"
bootstrap = Bootstrap(app)


# 查看所有用户消息
class ShowAllUser(MethodView):
    def get(self):
        DBSession = sessionmaker(bind=engine)
        session = DBSession()
        try:
            users = session.query(User).all()
        except Exception as e:
            return "服务器蹦了！"
        session.close()
        users.sort(key=lambda x: x.cf_rating, reverse=True)
        return render_template("all_user.html", users=[_.to_json() for _ in users])


# 添加用户
class AddUser(MethodView):
    def get(self):
        return render_template("add_user.html", bootstrap=bootstrap)

    def post(self):
        DBSession = sessionmaker(bind=engine)
        session = DBSession()
        user_name = request.values.get("user_name")
        class_pro = request.values.get("class_pro")
        cf_name = request.values.get("cf_name")
        cf_profile_url = "https://codeforces.com/profile/" + cf_name
        cf_rating = get_rating(cf_profile_url)
        if cf_rating == -1:
            flash("codeforces 用户不存在！")
            session.close()
            return redirect(url_for("show_all_user"))
        try:
            user = session.query(User).filter(User.user_name == user_name).first()
        except Exception:
            flash("因服务器太差，服务器挂了！")
            session.close()
            return redirect(url_for("show_all_user"))

        if user != None:
            flash("codeforces 用户已经添加！")
            session.close()
            return redirect(url_for("show_all_user"))

        user = User(user_name=user_name, class_pro=class_pro, cf_name=cf_name, cf_profile_url=cf_profile_url,
                    cf_rating=cf_rating)
        session.add(user)
        try:
            session.commit()
        except Exception:
            flash("因服务器太差，服务器挂了！")
            session.close()
            return redirect(url_for("show_all_user"))
        flash("添加成功！")
        session.close()
        return redirect(url_for("show_all_user"))


# 删除用户
class DeleteUser(MethodView):
    def post(self, id):
        token = request.cookies.get("token")
        if token != app.config["token"]:
            flash("不是管理员不能删除！")
            return redirect(url_for("show_all_user"))
        DBSession = sessionmaker(bind=engine)
        session = DBSession()
        user = session.query(User).filter(User.id == id).first()
        if user == None:
            flash("该用户不存在！")
            session.close()
            return redirect(url_for("show_all_user"))
        session.query(User).with_for_update().filter(User.id == id).delete()
        try:
            session.commit()
        except Exception:
            flash("因服务器太差，服务器挂了！")
            session.close()
            return redirect(url_for("show_all_user"))
        flash("删除成功！")
        session.close()
        time.sleep(1)
        return redirect(url_for("show_all_user"))


# 更新用户分数
class UpdateUser(MethodView):
    def get(self):
        DBSession = sessionmaker(bind=engine)
        session = DBSession()
        users = session.query(User).all()
        for user in users:
            user.cf_rating = get_rating(user.cf_profile_url)
            session.add(user)
        try:
            session.commit()
        except Exception:
            flash("因服务器太差，服务器挂了！")
            session.close()
            return redirect(url_for("show_all_user"))
        flash("刷新成功！")
        session.close()
        return redirect(url_for("show_all_user"))


class Login(MethodView):
    def get(self):
        return render_template("auth.html")

    def post(self):
        token = request.values.get("token")
        location = url_for("show_all_user")
        response = make_response(
            '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">\n'
            "<title>Redirecting...</title>\n"
            "<h1>Redirecting...</h1>\n"
            "<p>You should be redirected automatically to target URL: "
            '<a href="%s">%s</a>.  If not click the link.'
            % (escape(location),
               escape(location)), 302)
        response.set_cookie("token", token)
        response.headers["Location"] = location
        return response


app.add_url_rule("/add_user/", view_func=AddUser.as_view("add_user"))
app.add_url_rule("/update_user/", view_func=UpdateUser.as_view("update_user"))
app.add_url_rule("/show_all_user/", view_func=ShowAllUser.as_view("show_all_user"))
app.add_url_rule("/delete_user/<id>/", view_func=DeleteUser.as_view("delete_user"))
app.add_url_rule("/login/", view_func=Login.as_view("login"))


def get_rating(url):
    from requests_html import HTMLSession
    session = HTMLSession()
    r = session.get(url)

    sel1 = "#pageContent > div:nth-child(3) > div.userbox > div.info > ul > li:nth-child(1) > span.user-legendary"  # 黑红
    sel2 = "#pageContent > div:nth-child(3) > div.userbox > div.info > ul > li:nth-child(1) > span.user-red"  # 红
    sel3 = "#pageContent > div:nth-child(3) > div.userbox > div.info > ul > li:nth-child(1) > span.user-orange"  # 橙
    sel4 = "#pageContent > div:nth-child(3) > div.userbox > div.info > ul > li:nth-child(1) > span.user-violet"  # 紫
    sel5 = "#pageContent > div:nth-child(3) > div.userbox > div.info > ul > li:nth-child(1) > span.user-cyan"  # 蓝
    sel6 = "#pageContent > div:nth-child(3) > div.userbox > div.info > ul > li:nth-child(1) > span.user-blue"  # 绿
    sel7 = "#pageContent > div:nth-child(3) > div.userbox > div.info > ul > li:nth-child(1) > span.user-gray"  # 银
    sel8 = "#pageContent > div:nth-child(3) > div.userbox > div.info > ul > li:nth-child(1) > span.user-green"  # 绿
    sels = [sel1, sel2, sel3, sel4, sel5, sel6, sel7, sel8]
    for sel in sels:
        results = r.html.find(sel)
        if len(results) != 0:
            break
    if len(results) == 0:
        return -1
    return results[0].text


if __name__ == '__main__':
    app.run(debug=True, port=12345, host="0.0.0.0")
