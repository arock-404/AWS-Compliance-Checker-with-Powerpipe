import hashlib
import psycopg2
from psycopg2.extras import Json
from flask import Flask, request, jsonify
from subprocess import Popen, PIPE, STDOUT
import os
import json
import uuid
from datetime import datetime

app = Flask(__name__)

def set_aws_credentials():
    data = request.get_json()
    if data is None:
        return jsonify({'error': 'Invalid JSON'}), 400

    AWS_ACCESS_KEY_ID = data.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = data.get('AWS_SECRET_ACCESS_KEY')

    if not AWS_ACCESS_KEY_ID or not AWS_SECRET_ACCESS_KEY:
        return jsonify({'error': 'Missing AWS credentials'}), 400

    os.environ['AWS_ACCESS_KEY_ID'] = AWS_ACCESS_KEY_ID
    os.environ['AWS_SECRET_ACCESS_KEY'] = AWS_SECRET_ACCESS_KEY

def run_powerpipe():
    powerpipe_path = "/usr/local/bin/powerpipe"
    command = f'{powerpipe_path} benchmark run [ENTER YOUR COMPLIANCE BENCHMARK NAME (eg --> aws_compliance.benchmark.cis_v200)] --output json'

    try:
        process = Popen(command, shell=True, stdout=PIPE, stderr=STDOUT, env={
            'AWS_ACCESS_KEY_ID': os.environ['AWS_ACCESS_KEY_ID'],
            'AWS_SECRET_ACCESS_KEY': os.environ['AWS_SECRET_ACCESS_KEY']
        })
        output, _ = process.communicate()
        
        try:
            json_output = json.loads(output.decode())
        except json.JSONDecodeError as e:
            return jsonify({'error': 'Failed to parse JSON output', 'details': str(e)}), 500

        def uuid_to_bigint(uuid_val):
            # Hash the UUID and take the first 16 bytes (128 bits)
            hash_object = hashlib.sha256(uuid_val.encode())
            hex_digest = hash_object.hexdigest()
            uuid_hashed_int = int(hex_digest[:32], 16)  # 32 hex characters = 16 bytes = 128 bits
            return uuid_hashed_int & (2**63 - 1)  # Ensure it fits within signed 64-bit range
        request_id = uuid_to_bigint(str(uuid.uuid4()))
        added_date = datetime.now()

        def extract_controls(groups):
            controls_list = []
            for group in groups:
                if 'controls' in group and group['controls'] is not None:
                    for control in group['controls']:
                        # Extract the necessary fields
                        filtered_control = {
                            'control_id': control.get('control_id', ''),
                            'description': control.get('description', ''),
                            'results': control.get('results', []),
                            'summary': control.get('summary', {}),
                            'title': control.get('title', '')
                        }
                        controls_list.append(filtered_control)
                if 'groups' in group and group['groups'] is not None:
                    controls_list.extend(extract_controls(group['groups']))
            return controls_list
        
        parsed_result = extract_controls(json_output['groups'])
    
        save_to_database(request_id, added_date, json_output, parsed_result)

        return jsonify(json_output), 200
    except Exception as e:
        print(str(e))
        return jsonify({'error': str(e)}), 400

def save_to_database(request_id, added_date, json_output, parsed_result):
    conn = None
    try:
        conn = psycopg2.connect(
            dbname="postgres",  # Use your actual database name here
            user="postgres",   # Replace with your PostgreSQL username
            password="root",  # Replace with your PostgreSQL password
            host="192.168.***.***"    # Replace with your PostgreSQL host
        )
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO json_storage (requestid, added_date, json_result, parsed_result)
            VALUES (%s, %s, %s, %s)
        """, (request_id, added_date, Json(json_output), Json(parsed_result)))

        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Error saving to database: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.route('/run_powerpipe/', methods=['POST'])
def execute_powerpipe():
    response = set_aws_credentials()
    if response is not None:
        return response
    return run_powerpipe()

if __name__ == '__main__':
    app.run(debug=True)
