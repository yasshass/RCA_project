import pandas as pd
import numpy
from TestabMethods import *
from RcaValidation import *
#from GetData import *
data = pd.DataFrame(data={"variants" : [1,1,1,2,2,2],
                   "value" : [0.5, 2,2,1,2,3],
                   "comb1" : ["a", "b", "a", "a", "b", "b"]
    ,
                   "comb2": ["1", "1", "2", "2", "2", "1"]
                          }
             )

testdata = TestData(data,
                             variants_col = "variants",
                             var_cols = ["comb1", "comb2"],
                             metric_col = "value",
                             ref_var = 1)


testmethod = AbtestMethod(transformations["None"],
                          outliers_methods["M1"],
                          test_methods["welch_ttest"])

testdata.abtest(testmethod)
testdata.abtest_withcomb(testmethod)
rca = MicroTestRca(testmethod)






