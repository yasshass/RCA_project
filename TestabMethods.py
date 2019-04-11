# from scipy.stats import ttest_ind
import numpy as np
from scipy.stats import t
from scipy.stats import ttest_ind
import pandas as pd
from abc import *


class TestData:

    def __init__(self, data, variants_col, var_cols,
                 metric_col, ref_var, variants = None):
        """

        :type ref_var: string
        """
        self.data = data
        self.variants_col = variants_col
        self.var_cols = var_cols
        self.metric_col = metric_col
        self.ref_var = ref_var
        self.variants = list(np.unique(self.data[self.variants_col]))
        self.variants.remove(self.ref_var)
        self.struct = {'variants_col' : variants_col,
                       'var_cols' : var_cols,
                       'metric_col' : metric_col,
                       'ref_var' : ref_var,
                       'variants' : self.variants}

    def abtest(self, abtest_method):
        return abtest_method.get_testresults_from_testd(self)

    def abtest_withcomb(self, abtest_method):
        result = pd.DataFrame()
        result = (self
                  .data.groupby(self.var_cols)
                  .apply(abtest_method.get_testresults_fromdf,
                         **self.struct)
                  )
        return result

    def statistics_withcomb(self):
        result = (self
        .data.groupby(self.var_cols + [self.variants_col])[self.metric_col]
        .agg(['mean', 'count']))
        return result

class AbtestMethod:

    def __init__(self, trans, outliersmethod, testmethod):
        self.trans = trans
        self.outliersmethod = outliersmethod
        self.testmethod = testmethod

    def get_pvalue(self, v1, v2):
        v1_trans, v2_trans = self.trans(v1), self.trans(v2)
        v1_clean, v2_clean = self.outliersmethod(v1_trans, v2_trans)
        try:
            return self.testmethod(v1_clean, v2_clean)
        except:
            return None

    def get_testresults(self, v1, v2):
        m1, count1, p_value ,m2, count2 = float('nan'), 0, float('nan'), float('nan'), 0
        if len(v1)>0 and len(v2)>0:
            v1_trans, v2_trans = self.trans(v1), self.trans(v2)
            v1_clean, v2_clean = self.outliersmethod(v1_trans, v2_trans)
            m1, m2 = v1_clean.mean(), v2_clean.mean()
            count1, count2 = len(v1_clean), len(v2_clean)
            try:
                p_value = self.testmethod(v1_clean, v2_clean)
            except:
                p_value = None
        else:
            if len(v1)>0 :
                m1, count1 = v1.mean(), len(v1)
            if len(v2)>0 :
                m2, count2 = v2.mean(), len(v2)

        return m1, m2, round((m2 - m1) / m1, 3), count1, count2, p_value

    def get_testresults_fromdf(self, data, variants, metric_col,
                               variants_col, ref_var, **kwargs):
        dict_testvariants = {}
        for variant in variants:
            v1 = data[data[variants_col]
                               == ref_var][metric_col].values
            v2 = data[data[variants_col]
                               == variant][metric_col].values
            # print(v1, v2)
            result_att = ["mean_{}".format(ref_var),
                          "mean_{}".format(variant),
                          "diff_ratio",
                          "count_{}".format(ref_var),
                          "count_{}".format(variant),
                          "pvalue"
                          ]
            dict_testvariants[variant] = dict(
                zip(result_att, self.get_testresults(v1, v2)))
        return dict_testvariants

    def get_testresults_from_testd(self, TestData):

        return self.get_testresults_fromdf(TestData.data, **TestData.struct)


transformations = {"log": np.log,
                   "None": lambda x: x}

test_methods = {"welch_ttest": lambda v1, v2: welch_ttest(v1, v2)}

outliers_methods = {
    "M1": lambda v1, v2: drop_outliers(v1, v2),
    "M2": lambda v1, v2: drop_outliers(v1, v2, drop_outliers_std),
    "M3": lambda v1, v2: drop_outliers(
        v1, v2, lambda x: drop_outliers_std(x, log_limits=True)
    ),
    "M4": lambda v1, v2: drop_outliers(v1, v2, drop_outliers_quantiles),
    "M5": lambda v1, v2: drop_outliers(v1, v2, drop_outliers_MAD),
    "M6": lambda v1, v2: drop_outliers(v1, v2, drop_outliers_std,
                                       common_outliers=True),
    "M7": lambda v1, v2: drop_outliers(v1, v2, drop_outliers_quantiles,
                                       common_outliers=True),
    "M8": lambda v1, v2: drop_outliers(v1, v2, drop_outliers_MAD,
                                       common_outliers=True)
}


def welch_ttest(v1, v2):
    # m1, m2 = v1.mean() ,v2.mean()
    # print(v1, v2)
    ts, p_value = ttest_ind(v1, v2, equal_var=False)
    return p_value


def welch_ttest_rebuilt(v1, v2):
    m1, m2 = v1.mean(), v2.mean()
    n1, n2 = len(v1), len(v2)
    var1, var2 = n1 / (n1 - 1) * v1.var(), n2 / (n2 - 1) * v2.var()

    ts = np.absolute(m2 - m1) / np.sqrt(var1 / n1 + var2 / n2)
    v = ((var1 / n1 + var2 / n2) ** 2
         / (var1 ** 2 / n1 ** 2 / (n1 - 1) + var2 ** 2 / n2 ** 2 / (n2 - 1))
         )
    p_value = 2 * (1 - t.cdf(ts, v))
    return p_value


class OutliersDetector(ABC):
    left1 = - np.inf
    right1 = + np.inf
    common_outliers = False
    def __init__(self, common_outliers=False):
        self.common_outliers = common_outliers

    @abstractmethod
    def fit_univariate(self, v):
        return self.left1, self.right1

    @classmethod
    def fit_bivariate(self, v1, v2):
        if self.common_outliers:
            left_1, right_1 = left_2, right_2 = self.fit_univariate(
                np.append(v1, v2))
        else:
            left_1, right_1 = self.fit_univariate(v1)
            left_2, right_2 = self.fit_univariate(v2)

        self.left1, self.right1 = left_1, right_1
        self.left2, self.right2 = left_2, right_2

    @classmethod
    def drop_bivariate(self, v1, v2):
        v1_clean, v2_clean = (v1[(v1 > self.left1) & (v1 < self.right1)],
                              v2[(v2 > self.left1) & (v2 < self.right1)])
        return v1_clean, v2_clean

    @classmethod
    def drop_univariate(self, v1, v2):
        v1_clean = v1[(v1 > self.left1) & (v1 < self.right1)],
        return v1_clean


def drop_outliers(v1, v2, drop_outlier=None,
                  common_outliers=False):
    if drop_outlier is None:
        drop_outlier = lambda x: (x.min() - 1, x.max() + 1)
    if common_outliers:
        left_1, right_1 = left_2, right_2 = drop_outlier(np.append(v1, v2))
    else:
        left_1, right_1 = drop_outlier(v1)
        left_2, right_2 = drop_outlier(v2)
    v1_clean, v2_clean = (v1[(v1 > left_1) & (v1 < right_1)],
                          v2[(v2 > left_2) & (v2 < right_2)])
    return v1_clean, v2_clean


def drop_outliers_std(v, k=3, log_limits=False):
    if log_limits:
        log_v = np.log(v)
        m = log_v.mean()
        sd = log_v.std()
        return np.exp(m - k * sd), np.exp(m + k * sd)
    else:
        m = v.mean()
        sd = v.std()
        return (m - k * sd), (m + k * sd)


def drop_outliers_quantiles(v, q=5):
    return np.percentile(v, q), np.percentile(v, 100 - q)


def drop_outliers_MAD(v, k=3):
    median = np.median(v)
    mad = 1.486 * np.median(np.abs(v - median))
    return (median - k * mad), (median + k * mad)
