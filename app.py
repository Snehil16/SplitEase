from flask import Flask, render_template

app = Flask(__name__)
app.config.from_object('config.Config')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return render_template('signup_new.html')

@app.route('/addperson', methods=['GET', 'POST'])
def addperson():
    return render_template('addPerson.html')

@app.route('/contactus', methods=['GET', 'POST'])
def contactus():
    return render_template('contact_us_new.html')

@app.route('/people', methods=['GET', 'POST'])
def people():
    return render_template('people.html')

@app.route('/stats', methods=['GET', 'POST'])
def stats():
    return render_template('stats.html')

@app.route('/update_expense', methods=['GET', 'POST'])
def update_expense():
    return render_template('update_expense.html')

if __name__ == '__main__':
    app.run(debug=True)
