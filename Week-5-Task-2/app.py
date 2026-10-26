import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)

SPEECH_KEY = os.getenv('SPEECH_KEY', '').strip()
SPEECH_REGION = os.getenv('SPEECH_REGION', 'eastus').strip()


# Command Word to Math Symbol Mapping (as per assignment table)
WORD_TO_MATH = {
    'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
    'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
    'point': '.', 'dot': '.',
    'plus': '+', 'add': '+',
    'minus': '-', 'subtract': '-',
    'times': '*', 'multiply': '*', 'multiplied by': '*',
    'over': '/', 'divided by': '/', 'divide': '/',
    'is': '=', 'equals': '=', 'equal': '='
}

# Math Symbol to Spoken Word Mapping
MATH_TO_WORD = {
    '0': 'Zero', '1': 'One', '2': 'Two', '3': 'Three', '4': 'Four',
    '5': 'Five', '6': 'Six', '7': 'Seven', '8': 'Eight', '9': 'Nine',
    '.': 'Point',
    '+': 'plus',
    '-': 'minus',
    '*': 'times',
    'x': 'times',
    '×': 'times',
    '/': 'over',
    '÷': 'over',
    '=': 'is'
}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/calculate', methods=['POST'])
def calculate():
    """Calculates mathematical expression without using eval()."""
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    num1 = data.get('num1')
    operator = data.get('operator')
    num2 = data.get('num2')

    if num1 is None or num2 is None or operator is None:
        return jsonify({'error': 'Missing fields: num1, operator, num2 are required.'}), 400

    try:
        num1 = float(num1)
        num2 = float(num2)
    except (ValueError, TypeError):
        return jsonify({'error': 'Operands must be valid numbers.'}), 400

    # Clean operator
    op_clean = operator.strip().lower()

    if op_clean in ['+', 'plus']:
        result = num1 + num2
    elif op_clean in ['-', 'minus']:
        result = num1 - num2
    elif op_clean in ['*', 'x', '×', 'times']:
        result = num1 * num2
    elif op_clean in ['/', '÷', 'over']:
        if num2 == 0:
            return jsonify({'error': 'Division by zero is not allowed.'}), 400
        result = num1 / num2
    else:
        return jsonify({'error': f'Unsupported operator: {operator}'}), 400

    # Format result: convert whole numbers to int (e.g. 7.0 -> 7)
    if result == int(result):
        result = int(result)
    else:
        result = round(result, 4)

    return jsonify({
        'result': result,
        'spoken_result': f"is {result}"
    }), 200


@app.route('/api/voice-command', methods=['POST'])
def parse_voice_command():
    """
    Parses a recognized spoken text command (e.g. "Five plus two is" or "Nine over three is")
    and returns parsed operands, operator, and computed result.
    """
    data = request.get_json()
    if not data or not data.get('text', '').strip():
        return jsonify({'error': 'No voice command received.'}), 400

    raw_text = data.get('text').strip().lower()

    # Normalize punctuation and spaces
    for punct in [',', '.', '!', '?', ';']:
        raw_text = raw_text.replace(punct, ' ')

    tokens = raw_text.split()
    translated_tokens = []

    for t in tokens:
        if t in WORD_TO_MATH:
            translated_tokens.append(WORD_TO_MATH[t])
        elif t.isdigit():
            translated_tokens.append(t)
        elif t in ['+', '-', '*', '/', '=']:
            translated_tokens.append(t)

    # Reconstruct tokens: Expecting <num1> <op> <num2> [=]
    # Filter tokens into num1, op, num2
    nums = []
    op = None

    for t in translated_tokens:
        if t in ['+', '-', '*', '/']:
            op = t
        elif t == '=':
            pass
        else:
            nums.append(t)

    if len(nums) < 2 or not op:
        return jsonify({
            'error': f"Could not parse equation from '{data.get('text')}'. Expected format like 'Five plus two is'."
        }), 400

    try:
        n1 = float(nums[0])
        n2 = float(nums[1])
    except ValueError:
        return jsonify({'error': 'Invalid numeric values recognized.'}), 400

    # Compute
    if op == '+':
        res = n1 + n2
    elif op == '-':
        res = n1 - n2
    elif op == '*':
        res = n1 * n2
    elif op == '/':
        if n2 == 0:
            return jsonify({'error': 'Division by zero is not allowed.'}), 400
        res = n1 / n2

    if res == int(res):
        res = int(res)
    else:
        res = round(res, 4)

    return jsonify({
        'raw_text': data.get('text'),
        'num1': int(n1) if n1 == int(n1) else n1,
        'operator': '÷' if op == '/' else ('x' if op == '*' else op),
        'num2': int(n2) if n2 == int(n2) else n2,
        'result': res,
        'spoken_sentence': f"is {res}"
    }), 200


if __name__ == '__main__':
    # Try port 5000 first; if busy, switch to port 5002
    try:
        app.run(debug=True, port=5000)
    except OSError:
        print("Port 5000 busy, running on port 5002...")
        app.run(debug=True, port=5002)
