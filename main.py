import sqlite3

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from hashids import Hashids


def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


app = Flask(__name__)
app.config["SECRET_KEY"] = "for the night is dark and full of terrors"
app.config["JSON_SORT_KEYS"] = False

hashids = Hashids(min_length=4, salt=app.config["SECRET_KEY"])


@app.route("/", methods=("GET", "POST"))
def index():
    conn = get_db_connection()

    if request.method == "POST":
        url = request.form["url"]

        if not url:
            flash("please enter a URL!")
            return redirect(url_for("index"))

        url_data = conn.execute("INSERT INTO urls (original_url) VALUES (?)", (url,))
        conn.commit()
        conn.close()

        url_id = url_data.lastrowid
        hashid = hashids.encode(url_id)
        short_url = request.host_url + hashid

        return render_template("index.html", short_url=short_url)

    return render_template("index.html")


@app.route("/api/v1")
def api():
    conn = get_db_connection()

    url = request.args.get("url")

    if url != "":
        url_data = conn.execute("INSERT INTO urls (original_url) VALUES (?)", (url,))
        conn.commit()
        conn.close()

        url_id = url_data.lastrowid
        hashid = hashids.encode(url_id)
        short_url = request.host_url + hashid
        response_data = {
            "org_url": url,
            "short_url": short_url,
        }
        return jsonify(response_data)


@app.route("/<id>")
def url_redirect(id):
    conn = get_db_connection()

    original_id = hashids.decode(id)
    if original_id:
        original_id = original_id[0]
        url_data = conn.execute(
            "SELECT original_url, clicks FROM urls" " WHERE id = (?)", (original_id,)
        ).fetchone()
        original_url = url_data["original_url"]
        clicks = url_data["clicks"]

        conn.execute(
            "UPDATE urls SET clicks = ? WHERE id = ?", (clicks + 1, original_id)
        )

        conn.commit()
        conn.close()
        return redirect(original_url)
    else:
        flash("Invalid URL")
        return redirect(url_for("index"))


@app.route("/stats")
def stats():
    conn = get_db_connection()
    db_urls = conn.execute(
        "SELECT id, created, original_url, clicks FROM urls"
    ).fetchall()
    conn.close()

    urls = []
    for url in db_urls:
        url = dict(url)
        print(url)
        url["short_url"] = request.host_url + hashids.encode(url["id"])
        urls.append(url)

    return render_template("stats.html", urls=urls)


if __name__ == "__main__":
    app.run()
