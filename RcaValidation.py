from TestabMethods import *
from abc import *



class RcaMethod(ABC):
    """
            A abstract class used to represent an RCA method

            ...


            Methods
            -------
            fit(testdata)

                an abstract method that adds some attributes to the class with amin attribute decision
            abtest_withcomb(abtest_method)

            predict(vars_vals)
                return predicted variant
            """
    @abstractmethod
    def fit(self, testdata):
        return None

    def predict(self, vars_vals):
        return self.decision.loc[[tuple(_) for _ in vars_vals.values]].values
        print("predict_done")


    def fit_predict(self, testdata):
        self.fit(testdata)
        self.predict(testdata.data[testdata.var_cols])

    def evaluate_1(self, testdata):
        good_pred = testdata.data[
            self.predict(testdata.data[testdata.var_cols])==
            testdata.data[testdata.variants_col]
        ]
        good_pred = TestData(data=good_pred,**testdata.struct)
        return (good_pred.data[good_pred.metric_col].mean(),
                testdata.data[testdata.metric_col].mean()
                )




    def evaluate(self, testdata):
        comb_stat = testdata.statistics_withcomb()
        indexes = pd.MultiIndex.from_product([np.unique(testdata.data[col])
                                              for col in testdata.var_cols+[testdata.variants_col]]
                                             ).difference(comb_stat.index)
        comb_stat = comb_stat.append(pd.DataFrame(index=indexes, data={"mean": self.max_mean, "count": 0}))
        pred = testdata.data.copy()
        pred[testdata.variants_col] = self.predict(
            testdata.data[testdata.var_cols])

        comb_count = (pred.groupby(testdata.var_cols + [testdata.variants_col])[testdata.metric_col]
            .agg(['count']))
        indexes = pd.MultiIndex.from_product([np.unique(testdata.data[col])
                                              for col in testdata.var_cols+[testdata.variants_col]]
                                             ).difference(comb_count.index)
        comb_count = comb_count.append(pd.DataFrame(index=indexes, data={ "count": 0}))
        comb_count["mean"] = comb_stat["mean"]
        result = (comb_count["count"]*comb_count["mean"]).sum()/comb_count["count"].sum()
        #pred[testdata.metric_col] = comb_stat.loc(pred[testdata.var_cols + [testdata.variants_col]])['mean']

        return (result,
                testdata.data[testdata.metric_col].mean()
                )


class RandomAssign(RcaMethod):

    def __init__(self):
        RcaMethod.__init__(self)

    def fit(self, testdata):
        self.ref_var = testdata.ref_var
        self.variant = testdata.variants[0]
        self.proportion = testdata.data[testdata.variants_col].value_counts(normalize=True)
        self.ref_var = testdata.ref_var
        self.variant = testdata.variants[0]
        self.variant_mean = testdata.data[testdata.data[testdata.variants_col]==self.variant][
            testdata.metric_col].mean()
        self.ref_mean = testdata.data[testdata.data[testdata.variants_col] == self.ref_var][testdata.metric_col].mean()
        self.max_mean = max(self.variant_mean, self.ref_mean)
        self.max_variant = self.ref_var if self.variant_mean < self.max_mean else self.variant
        indexes = pd.MultiIndex.from_product([np.unique(testdata.data[col])
                                                                    for col in testdata.var_cols])
        self.decision = pd.Series(index=indexes,
                                  data=np.random.choice([self.ref_var, self.variant], size=len(indexes),
                                p=self.proportion.loc[[self.ref_var, self.variant]]),
                                  name="decision")
        print("fit_done")






class MicroTestRca(RcaMethod):

    def __init__(self, testmethod):
        self.testmethod = testmethod

    def fit(self, testdata):
        self.results = testdata.abtest_withcomb(self.testmethod)
        self.ref_var = testdata.ref_var
        self.variant = testdata.variants[0]
        self.variant_mean = testdata.data[testdata.data[testdata.variants_col]==self.variant][
            testdata.metric_col].mean()
        self.ref_mean = testdata.data[testdata.data[testdata.variants_col] == self.ref_var][testdata.metric_col].mean()
        self.max_mean = max(self.variant_mean, self.ref_mean)
        self.max_variant = self.ref_var if self.variant_mean < self.max_mean else self.variant
        self.decision = pd.Series(index=self.results.index,
                                  data=self.results.map(lambda x : self.max_variant if x[self.variant]["diff_ratio"]
        is None else self.ref_var if x[self.variant]["diff_ratio"] < 0 else self.variant))
