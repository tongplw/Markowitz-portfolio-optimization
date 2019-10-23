import markowitz as mk

a = open('input.csv')

o = mk.Optimizer(a)
# o.clean()
# o.convert_to_returns_df()
o.test()

