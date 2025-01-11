from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import platform
import subprocess
import os
import uuid
import re

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/')
def home():
    return render_template("home.html")

# Commands for different languages
LANGUAGE_COMMANDS = {
    'c': {'compile': 'gcc {source} -o {output}', 'execute': './{output}'},
}

@app.route('/run', methods=['POST'])
def run_code():
    data = request.json
    code = data.get('code', '')
    language = data.get('language', '')

    if language not in LANGUAGE_COMMANDS:
        return jsonify({'error': 'Unsupported language!'}), 400

    file_extension = {
        'c': 'c'
    }.get(language, 'txt')

    file_name = f"{uuid.uuid4().hex}.{file_extension}"
    output_name = f"{uuid.uuid4().hex}"
    
    if language == 'java':# Extract class name
          match = re.search(r'public\s+class\s+(\w+)', code)
          if not match:
                return jsonify({'error': 'Java code must contain a public class with a name matching the file.'}), 400
          class_name = match.group(1)
          file_name = f"{class_name}.java"
    try:
        # Write code to file
        with open(file_name, 'w') as f:
            f.write(code)

        # Compile code (if required)
        compile_command = LANGUAGE_COMMANDS[language].get('compile')
        if compile_command:
            compile_command = compile_command.format(source=file_name, output=output_name)
            compile_process = subprocess.run(
                compile_command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if compile_process.returncode != 0:
                return jsonify({'error': compile_process.stderr.decode('utf-8')}), 400

        # Prepare execution command
        execute_command = LANGUAGE_COMMANDS[language]['execute'].format(
            source=file_name, output=output_name, 
            class_name=file_name.split('.')[0]
        )
        run_process = subprocess.run(
            execute_command.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )

        # Capture output and errors
        output = run_process.stdout.decode('utf-8')
        error = run_process.stderr.decode('utf-8')

        return jsonify({'output': output.strip(), 'error': error.strip()})

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Execution timed out!'}), 408

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up generated files
        if os.path.exists(file_name):
            os.remove(file_name)
        if os.path.exists(output_name):
            os.remove(output_name)
        if platform.system() == 'Windows' and os.path.exists(f"{output_name}.exe"):
             os.remove(f"{output_name}.exe")
       

if __name__ == '__main__':
    app.run(debug=True)
