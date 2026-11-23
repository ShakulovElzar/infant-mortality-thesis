"""Modified Poisson regression (log link, robust SE) fitted on covariate-pattern counts.

Why counts: every covariate in Part 2 is a category. Births with the same
categories share one predicted risk mu. So the model can be fitted on one row
per pattern, with n = births and d = deaths in that pattern, instead of on
millions of single births. Estimates are identical.

Robust (sandwich, HC0) covariance, exact from counts:
  bread  A = sum_g n_g * mu_g * x_g x_g'
  meat   B = sum_g [ d_g (1 - mu_g)^2 + (n_g - d_g) mu_g^2 ] x_g x_g'
  cov    = A^-1 B A^-1
(the bracket is the sum of squared single-birth residuals y - mu in the pattern).
Zou (2004) "modified Poisson" = Poisson log-link model + this robust covariance.
"""
import numpy as np


def design(rows: dict, columns: list[str], reference: dict) -> tuple[np.ndarray, list[str]]:
    """Intercept + one 0/1 column per non-reference category.

    rows: {column: numpy array of category codes (strings or ints), one per pattern}
    reference: {column: reference category}
    """
    n = len(next(iter(rows.values())))
    mats, names = [np.ones((n, 1))], ["intercept"]
    for col in columns:
        vals = rows[col]
        cats = [c for c in sorted(set(vals.tolist()), key=str) if c != reference[col]]
        for c in cats:
            mats.append((vals == c).astype(np.float64)[:, None])
            names.append(f"{col}={c}")
    return np.hstack(mats), names


def fit(X: np.ndarray, n: np.ndarray, d: np.ndarray, max_iter: int = 100, tol: float = 1e-10) -> dict:
    """Fit log mu = X beta on pattern counts (n births, d deaths). Returns beta and covariances."""
    n, d = n.astype(np.float64), d.astype(np.float64)
    beta = np.zeros(X.shape[1])
    beta[0] = np.log(d.sum() / n.sum())
    for it in range(max_iter):
        mu = np.exp(X @ beta)
        score = X.T @ (d - n * mu)
        A = (X * (n * mu)[:, None]).T @ X
        step = np.linalg.solve(A, score)
        beta += step
        if np.max(np.abs(step)) < tol:
            break
    else:
        raise RuntimeError("modified Poisson did not converge")
    mu = np.exp(X @ beta)
    A = (X * (n * mu)[:, None]).T @ X
    B = (X * (d * (1 - mu) ** 2 + (n - d) * mu ** 2)[:, None]).T @ X
    A_inv = np.linalg.inv(A)
    return {"beta": beta, "cov_robust": A_inv @ B @ A_inv, "cov_model": A_inv, "iterations": it + 1,
            "max_mu": float(mu.max())}


def rr(result: dict, names: list[str], term: str) -> dict:
    """Risk ratio, 95% CI and SE(log RR) for one coefficient."""
    j = names.index(term)
    b, se = result["beta"][j], np.sqrt(result["cov_robust"][j, j])
    return {"term": term, "log_rr": b, "se": se, "rr": np.exp(b),
            "rr_lo": np.exp(b - 1.96 * se), "rr_hi": np.exp(b + 1.96 * se)}


def standardized_rd(result: dict, X: np.ndarray, n: np.ndarray, exposed: np.ndarray,
                    exposure_cols: list[int], draws: int = 1000, seed: int = 20261123) -> dict:
    """g-computation risk difference per 1,000 births, standardized to the exposed patterns.

    For births in exposed patterns: predicted risk as observed minus predicted risk
    with the exposure columns set to 0 (reference). CI from coefficient draws
    from N(beta, robust covariance).
    """
    Xe, ne = X[exposed], n[exposed].astype(np.float64)
    X0 = Xe.copy()
    X0[:, exposure_cols] = 0.0

    def rd(beta):
        return 1000 * np.sum(ne * (np.exp(Xe @ beta) - np.exp(X0 @ beta))) / ne.sum()

    rng = np.random.default_rng(seed)
    sims = rng.multivariate_normal(result["beta"], result["cov_robust"], size=draws)
    vals = np.array([rd(b) for b in sims])
    return {"rd_per_1000": rd(result["beta"]), "rd_lo": np.percentile(vals, 2.5), "rd_hi": np.percentile(vals, 97.5)}
