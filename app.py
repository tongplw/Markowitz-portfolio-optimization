from flask import Flask, jsonify, request, render_template
from flask_csv import send_csv
from werkzeug.utils import secure_filename

import pandas as pd
import numpy as np
import datetime
import pandas_datareader as pdr
from cvxpy import Parameter, Variable, quad_form, Problem, Minimize, Maximize


def getReturns(stocks):

    w = pd.DataFrame()
    t = []
    for s in stocks:
        data = pdr.get_data_yahoo(
            s, 
            start=datetime.datetime(2009, 1, 1), 
            end=datetime.date.today(),
            interval='d'
        )
        px = data[['Close']]

        t.append(px)
    w = pd.concat(t,axis=1, join='inner')
    w = w.sort_index().pct_change()  #returns => w.cov() covariance matrix of returns

    betas = []
    returns = w

    return returns, stocks, np.round(betas,4)

def calculate_portfolio(cvxtype, returns_function, long_only, exp_return, 
                        selected_solver, max_pos_size, ticker_list):
    assert cvxtype in ['minimize_risk','maximize_return']
    
    """ Variables:
        mu is the vector of expected returns.
        sigma is the covariance matrix.
        gamma is a Parameter that trades off risk and return.
        x is a vector of stock holdings as fractions of total assets.
    """
    
    gamma = Parameter(nonneg=True)
    gamma.value = 1
    returns, stocks, betas = returns_function
        
    cov_mat = returns.cov()
    Sigma = cov_mat.values # np.asarray(cov_mat.values) 
    w = Variable(len(cov_mat))  # #number of stocks for portfolio weights
    risk = quad_form(w, Sigma)  #expected_variance => w.T*C*w =  quad_form(w, C)
    # num_stocks = len(cov_mat)
    
    if cvxtype == 'minimize_risk': # Minimize portfolio risk / portfolio variance
        if long_only == True:
            prob = Problem(Minimize(risk), [sum(w) == 1, w > 0 ])  # Long only
        else:
            prob = Problem(Minimize(risk), [sum(w) == 1]) # Long / short 
    
    elif cvxtype == 'maximize_return': # Maximize portfolio return given required level of risk
        #mu  #Expected return for each instrument
        #expected_return = mu*x
        #risk = quad_form(x, sigma)
        #objective = Maximize(expected_return - gamma*risk)
        #p = Problem(objective, [sum_entries(x) == 1])
        #result = p.solve()

        mu = np.array([exp_return]*len(cov_mat)) # mu is the vector of expected returns.
        expected_return = np.reshape(mu,(-1,1)).T * w  # w is a vector of stock holdings as fractions of total assets.   
        objective = Maximize(expected_return - gamma*risk) # Maximize(expected_return - expected_variance)
        if long_only == True:
            constraints = [sum(w) == 1, w > 0]
        else: 
            #constraints=[sum_entries(w) == 1,w <= max_pos_size, w >= -max_pos_size]
            constraints=[sum(w) == 1]
        prob = Problem(objective, constraints)

    prob.solve(solver=selected_solver)
    
    weights = []

    for weight in w.value:
        weights.append(float(weight))
        
    if cvxtype == 'maximize_return':
        optimal_weights = {"Optimal expected return":expected_return.value,
                        "Optimal portfolio weights":np.round(weights,2),
                        "tickers": ticker_list,
                        "Optimal risk": risk.value*100
                        }
        
    elif cvxtype == 'minimize_risk':
        optimal_weights = {"Optimal portfolio weights":np.round(weights,2),
                        "tickers": ticker_list,
                        "Optimal risk": risk.value*100
                        }   
    return optimal_weights
        
def optimize(stocks):
    stocks = stocks.split(",")

    for i in range(len(stocks)):
        stocks[i] = stocks[i].strip() + '.BK'

    ret = getReturns(stocks)
 
    # get portfolio weights
    p = calculate_portfolio(cvxtype='maximize_return',
                            returns_function=ret,
                            long_only=False,
                            exp_return=0.20,
                            selected_solver='SCS',
                            max_pos_size=0.50,
                            ticker_list=stocks)
                            
    n = len(p['Optimal portfolio weights'])
    return {p['tickers'][i]: p['Optimal portfolio weights'][i] for i in range(n)}


app = Flask(__name__)

@app.route('/', methods=['GET'])
def upload():
    return render_template('upload.html')

@app.route('/uploader', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':

        stocks = request.form['stocks_list']
        alloc = optimize(stocks)

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
