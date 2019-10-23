import math
import pandas as pd
import numpy as np
from cvxpy import *
# from posdef import nearestPD


class Optimizer(object):

    def __init__(self, file):
        self.prices_df = pd.read_csv(file)
        self.clean()
        self.compute_returns_df() # self.returns_df
        self.compute_annual_return() # self.annual_return
        self.compute_variance() #self.variance
        self.compute_covariance() # self.covariance
        # print(
        #     self.annual_return, 
        #     self.variance,
        #     self.covariance
        # )
        self.portfolio_alloc = self.compute_optimal_solution(
            self.annual_return, 
            self.variance,
            self.covariance
        )

    def clean(self):
        """ delete all the unused column."""
        for i in self.prices_df.columns:
            if '.BK' not in i:
                del self.prices_df[i]
                
    def compute_returns_df(self):
        """ return dataframe
            Calculated by: ln(day[i] / day[i - 1])
        """
        tem_dict = {}
        for i in self.prices_df.columns:
            if i not in tem_dict:
                tem_dict[i] = []
            for j in range(self.prices_df.shape[0] - 1):
                ret_value = math.log(self.prices_df[i][j+1] / self.prices_df[i][j])
                tem_dict[i].append(ret_value)
        self.returns_df = pd.DataFrame(tem_dict)
    
    def compute_annual_return(self):
        """ annual return
            Calculated by: avg(stock_return) * 365
        """
        self.annual_return = self.returns_df.mean() #* 365

    def compute_variance(self):
        self.variance = self.returns_df.var()

    def compute_covariance(self):
        self.covariance = self.returns_df.cov()

    def compute_optimal_solution(self, mean, variance, covariance):
        n = mean.size
        w = Variable(n, nonneg=True)
        constraints = [
            sum(w) == 1
        ]

        def cal_sharp_ratio(w, interest_rate=0.03):
            expected_ret = 0
            try:
                for stock, weight in zip(mean, w):
                    expected_ret += stock * weight
            except ValueError as e:
                pass
            # print(expected_ret)

            # sd = 0
            # for cov_col, weight_1 in zip(covariance, w):
            #     for weight_2, cov_val in zip(w, covariance[cov_col]):
            #         sd += weight_2 * cov_val * weight_1
            # # print(sd)
            # return (expected_ret - interest_rate/12) / square(sd)
            sd = 1
            return (expected_ret - interest_rate/12) / sqrt(sd)

        obj = Maximize(cal_sharp_ratio(w))
        prob = Problem(obj, constraints)
        prob.solve()
        # print(w.value)
        return {name:weight for name, weight in zip(covariance.columns, w.value)}

    def test(self):
        print(self.portfolio_alloc)