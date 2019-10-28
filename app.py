from flask import Flask, jsonify, request, render_template
from werkzeug import secure_filename
import codecs
import markowitz as mk
import pandas
from flask_csv import send_csv

app = Flask(__name__)

@app.route('/', methods=['GET'])
def upload():
   return render_template('upload.html')

@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        f = request.files['file']
        f.save(secure_filename(f.filename))

        a = open(f.filename)
        opt = mk.Optimizer(a)
        alloc = opt.portfolio_alloc
                
        output_type = request.form.get('select')

        if output_type == 'json':
            return alloc

        else:
            return send_csv(
                [{"stock": i, "weight": alloc[i]} for i in alloc],
                "test.csv",
                ["stock", "weight"]
            )

if __name__ == '__main__':
    app.run(debug=True)