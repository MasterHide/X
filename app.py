from flask import Flask, request, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)

db_path = "/etc/x-ui/x-ui.db"  # Change this if your database is located elsewhere

# Function to convert bytes to a human-readable format (B, KB, MB, GB, TB)
def convert_bytes(bytes_value):
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024 * 1024:
        return f"{bytes_value / 1024:.2f} KB"
    elif bytes_value < 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024):.2f} MB"
    elif bytes_value < 1024 * 1024 * 1024 * 1024:
        return f"{bytes_value / (1024 * 1024 * 1024):.2f} GB"
    else:
        return f"{bytes_value / (1024 * 1024 * 1024 * 1024):.2f} TB"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/usage', methods=['POST'])
def usage():
    user_input = request.form.get('user_input')  # Get input from the form

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query to fetch client data from client_traffics
    query = '''SELECT email, up, down, total, expiry_time, inbound_id FROM client_traffics WHERE email = ? OR id = ?'''
    cursor.execute(query, (user_input, user_input))

    row = cursor.fetchone()

    if row:
        email = row[0]
        up = row[1]
        down = row[2]
        total = row[3]
        expiry_date = datetime.utcfromtimestamp(row[4]).strftime('%Y-%m-%d %H:%M:%S')
        inbound_id = row[5]  # Get the inbound_id to query the inbounds table for totalGB

        # Query to fetch totalGB from inbounds table based on inbound_id
        inbound_query = '''SELECT settings FROM inbounds WHERE id = ?'''
        cursor.execute(inbound_query, (inbound_id,))
        inbound_row = cursor.fetchone()

        totalGB = "Not Available"  # Default value if totalGB is not found

        if inbound_row:
            # The totalGB is stored in the 'settings' column as a JSON structure
            import json
            settings_data = json.loads(inbound_row[0])
            for client in settings_data.get('clients', []):
                if client.get('email') == email:
                    totalGB = client.get('totalGB', "Not Available")
                    break

        # Convert up, down, total, and totalGB to human-readable format
        up_converted = convert_bytes(up)
        down_converted = convert_bytes(down)
        total_converted = convert_bytes(total)
        totalGB_converted = convert_bytes(totalGB)

        conn.close()

        return render_template('result.html', email=email, up=up_converted, down=down_converted, total=total_converted, expiry_date=expiry_date, totalGB=totalGB_converted)
    else:
        conn.close()
        return "No data found for this user."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
