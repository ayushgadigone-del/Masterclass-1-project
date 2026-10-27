"""
models_numpy.py
---------------
Pure-NumPy ML model implementations used by both train_model.py and app.py.
No scikit-learn / scipy dependency required.
"""

import numpy as np


class LinearRegressionNumpy:
    """Ordinary Least Squares via the normal equation."""
    name = "Linear Regression"

    def fit(self, X, y):
        Xb = np.column_stack([np.ones(len(X)), X])
        self.w_ = np.linalg.lstsq(Xb, y, rcond=None)[0]
        return self

    def predict(self, X):
        Xb = np.column_stack([np.ones(len(X)), X])
        return Xb @ self.w_


class DecisionTreeRegressorNumpy:
    """A simple CART regression tree (variance reduction)."""

    def __init__(self, max_depth=5, min_samples_split=2):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.tree_ = None

    def fit(self, X, y):
        self.tree_ = self._build(X, y, depth=0)
        return self

    def predict(self, X):
        return np.array([self._predict_one(x, self.tree_) for x in X])

    # ── internal helpers ──────────────────────────────────────────────────────
    def _build(self, X, y, depth):
        if (depth >= self.max_depth
                or len(y) < self.min_samples_split
                or np.unique(y).size == 1):
            return {"leaf": True, "value": float(np.mean(y))}

        best = self._best_split(X, y)
        if best is None:
            return {"leaf": True, "value": float(np.mean(y))}

        fi, thr = best
        left  = X[:, fi] <= thr
        right = ~left
        return {
            "leaf":  False,
            "fi":    fi,
            "thr":   thr,
            "left":  self._build(X[left],  y[left],  depth + 1),
            "right": self._build(X[right], y[right], depth + 1),
        }

    def _best_split(self, X, y):
        best_gain, best_fi, best_thr = -np.inf, None, None
        base_var = np.var(y) * len(y)
        for fi in range(X.shape[1]):
            for thr in np.unique(X[:, fi]):
                left  = X[:, fi] <= thr
                right = ~left
                if left.sum() == 0 or right.sum() == 0:
                    continue
                gain = base_var - (np.var(y[left])  * left.sum()
                                 + np.var(y[right]) * right.sum())
                if gain > best_gain:
                    best_gain, best_fi, best_thr = gain, fi, thr
        if best_fi is None:
            return None
        return best_fi, best_thr

    def _predict_one(self, x, node):
        if node["leaf"]:
            return node["value"]
        return (self._predict_one(x, node["left"])
                if x[node["fi"]] <= node["thr"]
                else self._predict_one(x, node["right"]))


class RandomForestRegressorNumpy:
    """Bootstrap-aggregating ensemble of DecisionTreeRegressorNumpy trees."""
    name = "Random Forest"

    def __init__(self, n_estimators=50, max_depth=5, random_state=42):
        self.n_estimators = n_estimators
        self.max_depth    = max_depth
        self.rng          = np.random.default_rng(random_state)
        self.trees_       = []

    def fit(self, X, y):
        self.trees_ = []
        n = len(X)
        for _ in range(self.n_estimators):
            idx  = self.rng.integers(0, n, size=n)
            tree = DecisionTreeRegressorNumpy(max_depth=self.max_depth)
            tree.fit(X[idx], y[idx])
            self.trees_.append(tree)
        return self

    def predict(self, X):
        preds = np.stack([t.predict(X) for t in self.trees_], axis=1)
        return preds.mean(axis=1)
