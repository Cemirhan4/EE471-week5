import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables from .env (check current dir, then parent)
load_dotenv()
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

app = Flask(__name__)

SPEECH_KEY = os.getenv('SPEECH_KEY', '').strip()
SPEECH_REGION = os.getenv('SPEECH_REGION', 'eastus').strip()


# Command Word to Math Symbol Mapping (as per assignment table)
WORD_TO_MATH = {
    'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
    'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
    'ten': '10', 'eleven': '11', 'twelve': '12',
    'point': '.', 'dot': '.',
    'plus': '+', 'add': '+',
    'minus': '-', 'subtract': '-',
    'times': '*', 'multiply': '*', 'multiplied by': '*',
    'over': '/', 'divided by': '/', 'divide by': '/', 'divided': '/', 'divide': '/', 'slash': '/', 'by': '/',
    'hour': '/', 'our': '/',
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
    import re

    data = request.get_json()
    if not data or not data.get('text', '').strip():
        return jsonify({'error': 'No voice command received.'}), 400

    raw_text = data.get('text').strip().lower()
    print(f"[VOICE COMMAND DEBUG] Raw text received: '{raw_text}'")

    # Step 1: Replace multi-word math phrases first before splitting
    phrases = [
        ('divided by', ' / '),
        ('divide by', ' / '),
        ('divided', ' / '),
        ('multiplied by', ' * '),
        ('multiply by', ' * '),
        ('times by', ' * '),
        ('plus', ' + '),
        ('minus', ' - '),
        ('times', ' * '),
        ('multiply', ' * '),
        ('over', ' / '),
        ('slash', ' / '),
        ('equals', ' = '),
        ('equal', ' = '),
        ('is', ' = ')
    ]
    for ph, rep in phrases:
        raw_text = re.sub(r'\b' + re.escape(ph) + r'\b', rep, raw_text)

    # Step 2: Ensure spaces around math symbols so "9/3" -> "9 / 3" or "5+2" -> "5 + 2"
    for sym in ['+', '-', '*', '/', '÷', '×', '=']:
        raw_text = raw_text.replace(sym, f' {sym} ')

    # Step 3: Handle single 'x' as multiplication (e.g. "3 x 2")
    raw_text = re.sub(r'\bx\b', ' * ', raw_text)

    # Step 4: Remove unwanted punctuation but keep dots for decimals
    for punct in [',', '!', '?', ';', ':', '"', "'"]:
        raw_text = raw_text.replace(punct, ' ')

    tokens = raw_text.split()
    translated_tokens = []

    for t in tokens:
        if t in WORD_TO_MATH:
            translated_tokens.append(WORD_TO_MATH[t])
        elif re.match(r'^-?\d+(\.\d+)?$', t):
            translated_tokens.append(t)
        elif t in ['+', '-', '*', '/', '=']:
            translated_tokens.append(t)
        elif t == '÷':
            translated_tokens.append('/')
        elif t == '×':
            translated_tokens.append('*')

    # Reconstruct: Find numbers and operator
    nums = []
    op = None

    for t in translated_tokens:
        if t in ['+', '-', '*', '/']:
            op = t
        elif t == '=':
            pass
        else:
            nums.append(t)

    # If operator is still missing but we have 2 numbers and raw text contains "over", "by", etc.
    if not op and len(nums) >= 2:
        if any(w in data.get('text', '').lower() for w in ['over', 'divide', 'div', '/']):
            op = '/'
        elif any(w in data.get('text', '').lower() for w in ['times', 'multi', '*', 'x']):
            op = '*'
        elif any(w in data.get('text', '').lower() for w in ['plus', 'add', '+']):
            op = '+'
        elif any(w in data.get('text', '').lower() for w in ['minus', 'sub', '-']):
            op = '-'

    if len(nums) < 2 or not op:
        print(f"[VOICE COMMAND DEBUG] Failed to parse. nums={nums}, op={op}, translated={translated_tokens}")
        return jsonify({
            'error': f"Could not parse equation from '{data.get('text')}'. Expected format like 'Nine over three is'."
        }), 400

    try:
        n1 = float(nums[0])
        n2 = float(nums[1])
    except ValueError:
        return jsonify({'error': 'Invalid numeric values recognized.'}), 400

    # Safe computation without eval()
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
    app.run(host='0.0.0.0', port=5002, debug=True)
