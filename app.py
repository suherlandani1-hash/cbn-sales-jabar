from flask import Flask, render_template, request, jsonify
import sqlite3
import math
import os

app = Flask(__name__)


DATABASE = r"C:\Users\HP\Downloads\Coverage cbn\database\coverage.db"


def hitung_jarak(lat1, lon1, lat2, lon2):

    R = 6371000

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(dlambda / 2) ** 2
    )

    c = 2 * math.atan2(
        math.sqrt(a),
        math.sqrt(1 - a)
    )

    return R * c


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/cek-coverage")
def cek_coverage():
    return render_template("cek.html")


@app.route("/api/cek-coverage", methods=["POST"])
def api_cek_coverage():

    try:

        data = request.get_json()

        latitude = float(data.get("latitude"))
        longitude = float(data.get("longitude"))

    except Exception:

        return jsonify({
            "success": False,
            "message": "Koordinat lokasi tidak valid."
        }), 400


    if not os.path.exists(DATABASE):

        return jsonify({
            "success": False,
            "message": "Database coverage tidak ditemukan.",
            "database": DATABASE
        }), 500


    try:

        conn = sqlite3.connect(DATABASE)

        conn.row_factory = sqlite3.Row

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                province,
                city,
                subdistrict,
                village,
                street,
                number,
                postal_code,
                notes,
                homeid,
                coordinate,
                project_id,
                project_name,
                cust_status,
                latitude,
                longitude
            FROM coverage
            WHERE latitude IS NOT NULL
              AND longitude IS NOT NULL
        """)

        rows = cursor.fetchall()

        conn.close()


        if not rows:

            return jsonify({
                "success": False,
                "message": "Data koordinat coverage belum tersedia."
            })


        hasil = []


        for row in rows:

            try:

                lat = float(row["latitude"])
                lon = float(row["longitude"])

            except (TypeError, ValueError):

                continue


            jarak = hitung_jarak(
                latitude,
                longitude,
                lat,
                lon
            )


            hasil.append({
                "jarak": jarak,
                "homeid": row["homeid"],
                "latitude": lat,
                "longitude": lon,
                "province": row["province"],
                "city": row["city"],
                "subdistrict": row["subdistrict"],
                "village": row["village"],
                "street": row["street"],
                "number": row["number"],
                "postal_code": row["postal_code"],
                "notes": row["notes"],
                "project_id": row["project_id"],
                "project_name": row["project_name"],
                "cust_status": row["cust_status"]
            })


        if not hasil:

            return jsonify({
                "success": False,
                "message": "Tidak ditemukan data koordinat coverage."
            })


        hasil.sort(
            key=lambda x: x["jarak"]
        )


        terdekat = hasil[0]

        jarak = terdekat["jarak"]


        if jarak <= 100:

            status = "COVERAGE TERSEDIA"
            status_class = "available"
            status_icon = "✅"

        elif jarak <= 300:

            status = "PERLU SURVEY"
            status_class = "survey"
            status_icon = "⚠️"

        else:

            status = "COVERAGE JAUH"
            status_class = "far"
            status_icon = "❌"


        terdekat["jarak_meter"] = round(jarak)
        terdekat["status"] = status
        terdekat["status_class"] = status_class
        terdekat["status_icon"] = status_icon


        return jsonify({

            "success": True,

            "customer_location": {
                "latitude": latitude,
                "longitude": longitude
            },

            "hasil": terdekat

        })


    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )