from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/userdashboard', methods=['POST', 'GET'])
def user_dashboard():
    user_data = {"username": 'Shubham Atkal'}
    if request.method == 'POST':
        return render_template('userdash.html', user=user_data)
    elif request.method == 'GET':
        # Handle the POST request here
        # Add your code to process the form data
        return render_template('userdash.html', user=user_data)

@app.route('/user/books', methods=['POST', 'GET'])
def user_books():
    user_data = {"username": 'Shubham Atkal'}
    return render_template('userbooks.html', user=user_data)

@app.route('/library/login')
def librarian_login():
    return render_template('liblogin.html')

@app.route('/library/register')
def librarian_register():
    return render_template('registerlib.html')

@app.route('/library/home', methods=['POST'])
def librarian_dashboard():
    return render_template('libdash.html')

@app.route('/forgot_password')
def forgot_password():
    return render_template('forgot_password.html')

if __name__ == '__main__':
    app.run(debug=True, port=3000)