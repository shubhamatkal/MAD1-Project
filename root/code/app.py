from flask import Flask, render_template

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

@app.route('/userdashboard', methods=['POST'])
def user_dashboard():
    user_data = {}
    return render_template('userdash.html', user=user_data)

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