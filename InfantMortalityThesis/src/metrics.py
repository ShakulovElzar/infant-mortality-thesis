"""Fast weighted metrics for very large test sets, and calibration.

The bootstrap uses Poisson(1) weights: each test birth gets a random count
(0, 1, 2, ...) that says how often it appears in a resample. This is the
standard fast approximation of resampling with replacement when n is large.
Scores are sorted once per model; each resample then needs only cumulative sums.
"""
import numpy as np
import statsmodels.api as sm


class SortedScores:
    """Pre-sorted scores of one model, for repeated weighted AP / ROC-AUC."""

    def __init__(self, y, p):
        order = np.argsort(-p, kind="stable")
        self.order = order
        self.y = y[order].astype(np.float64)
        ps = p[order]
        # last index of each group of tied scores
        self.ends = np.flatnonzero(np.r_[ps[1:] != ps[:-1], True])

    def metrics(self, w=None):
        """Return (average precision, ROC-AUC) for weights w (None = all 1)."""
        w = np.ones_like(self.y) if w is None else w[self.order]
        tp = np.cumsum(w * self.y)[self.ends]
        fp = np.cumsum(w * (1 - self.y))[self.ends]
        P, N = tp[-1], fp[-1]
        recall = tp / P
        # A bootstrap resample can give the top-scored group zero weight (0/0).
        # Recall does not change there, so its precision adds nothing; set it to 0.
        precision = np.divide(tp, tp + fp, out=np.zeros_like(tp), where=(tp + fp) > 0)
        ap = np.sum(np.diff(np.r_[0.0, recall]) * precision)
        tpr, fpr = np.r_[0.0, recall], np.r_[0.0, fp / N]
        auc = np.sum(np.diff(fpr) * (tpr[1:] + tpr[:-1]) / 2)
        return ap, auc


def brier(y, p, w=None):
    w = np.ones_like(p) if w is None else w
    return float(np.sum(w * (p - y) ** 2) / np.sum(w))


def calibration(y, p):
    """Calibration intercept (calibration-in-the-large) and slope, with 95% CIs.

    Slope: logistic regression of y on logit(p); 1 = perfect.
    Intercept: logistic regression of y with logit(p) as offset; 0 = perfect.
    """
    p = np.clip(p, 1e-7, 1 - 1e-7)
    lp = np.log(p / (1 - p))
    (a, b), cov_s = _logit_newton(y, lp, offset=False)
    (c,), cov_i = _logit_newton(y, lp, offset=True)
    se_b, se_c = np.sqrt(cov_s[1, 1]), np.sqrt(cov_i[0, 0])
    return {"cal_slope": b, "cal_slope_lo": b - 1.96 * se_b, "cal_slope_hi": b + 1.96 * se_b,
            "cal_intercept": c, "cal_intercept_lo": c - 1.96 * se_c, "cal_intercept_hi": c + 1.96 * se_c,
            "observed_over_expected": float(y.sum() / p.sum())}


def _logit_newton(y, lp, offset, iters=50):
    """Maximum-likelihood logistic fit with 1-2 parameters, low memory.

    offset=False: logit P(y) = a + b*lp   (returns a, b)
    offset=True:  logit P(y) = c + lp     (returns c)
    Returns the estimates and their covariance (inverse Hessian).
    Same model as statsmodels GLM Binomial; statsmodels needs too much memory at 7 M rows.
    """
    beta = np.array([0.0, 1.0]) if not offset else np.array([0.0])
    for _ in range(iters):
        eta = (beta[0] + beta[1] * lp) if not offset else (beta[0] + lp)
        mu = 1.0 / (1.0 + np.exp(-eta))
        r, v = y - mu, mu * (1 - mu)
        if offset:
            g, H = np.array([r.sum()]), np.array([[v.sum()]])
        else:
            g = np.array([r.sum(), (r * lp).sum()])
            H = np.array([[v.sum(), (v * lp).sum()], [(v * lp).sum(), (v * lp * lp).sum()]])
        step = np.linalg.solve(H, g)
        beta = beta + step
        if np.max(np.abs(step)) < 1e-10:
            break
    return beta, np.linalg.inv(H)
