from flask import Blueprint, request, jsonify
import requests
import mysql.connector
from flask import current_app
main = Blueprint('main', __name__)


connected_ips = {}

def get_db_connection():
    connection = mysql.connector.connect(
        host=current_app.config['MYSQL_HOST'],
        user=current_app.config['MYSQL_USER'],
        password=current_app.config['MYSQL_PASSWORD'],
        database=current_app.config['MYSQL_DB']
    )
    return connection

@main.route('/update', methods=['POST'])
def update():
    client_ip = request.remote_addr
    if 'ip' in request.json and 'color' in request.json:
        client_ip = request.json['ip']
        client_color = request.json['color']

        # Connect to MySQL database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if the IP is already registered
        cursor.execute('SELECT * FROM connected_ips WHERE ip = %s', (client_ip,))
        ip_exists = cursor.fetchone()

        if ip_exists:
            # Update color for the existing IP
            cursor.execute('UPDATE connected_ips SET color = %s WHERE ip = %s', (client_color, client_ip))
            conn.commit()
        else:
            # Register new IP
            cursor.execute('INSERT INTO connected_ips (ip, color) VALUES (%s, %s)', (client_ip, client_color))
            conn.commit()

        cursor.close()
        conn.close()
        return jsonify({"message": "IP updated or registered!", "ip": client_ip}), 200
    return jsonify({"message": "IP or color missing in request."}), 400

@main.route('/register', methods=['POST'])
def register():
    client_ip = request.remote_addr
    if 'ip' in request.json:
        client_ip = request.json['ip']
        client_color = request.json.get('color', 'blue')  # Default to 'blue' if color is not specified

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM connected_ips WHERE ip = %s', (client_ip,))
        ip_exists = cursor.fetchone()

        if not ip_exists:
            cursor.execute('INSERT INTO connected_ips (ip, color) VALUES (%s, %s)', (client_ip, client_color))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"message": "IP registered!", "ip": client_ip}), 201
        else:
            cursor.close()
            conn.close()
            return jsonify({"message": "IP already registered."}), 200
    return jsonify({"message": "IP missing in request."}), 400

@main.route('/broadcast', methods=['POST'])
def broadcast():
    message = request.json.get('message', 'BROAD')
    failed_ips = []


    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT ip FROM connected_ips')
    ip_list = cursor.fetchall()

    for ip_record in ip_list:
        ip = ip_record['ip']
        try:
            response = requests.post(f"http://{ip}:5000/receive", json={"message": message})
            if response.status_code != 200:
                failed_ips.append(ip)
        except Exception as e:
            failed_ips.append(ip)

    cursor.close()
    conn.close()

    if failed_ips:
        return jsonify({"message": "Broadcast completed with errors.", "failed_ips": failed_ips}), 207
    return jsonify({"message": "Broadcast successful!"}), 200

@main.route('/connections', methods=['GET'])
def list_connections():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT ip, color FROM connected_ips')
    connections = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"connected_ips": connections}), 200





