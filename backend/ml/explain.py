"""SHAP explanations for the Random Forest (2.2.7), shared by the reports and the web app.

SHAP gives each input a contribution to one class's predicted probability; the
contributions plus the model's average prediction add up to the prediction itself.
Contributions of helper columns (a "was missing" flag, one-hot level columns) are
summed back into the input they came from, so every explanation speaks in terms
of the variables a lecturer recognises.
"""
import numpy as np
import shap

from .models import source_feature


class Explainer:
    def __init__(self, pipeline, features):
        self.prep = pipeline.named_steps["prep"]
        self.clf = pipeline.named_steps["clf"]
        self.features = list(features)
        self.classes = [str(c) for c in self.clf.classes_]
        columns = list(self.prep.get_feature_names_out())
        self._source_index = [self.features.index(source_feature(c, self.features)) for c in columns]
        self._tree = shap.TreeExplainer(self.clf)

    def base_value(self, class_name):
        return float(np.asarray(self._tree.expected_value)[self.classes.index(class_name)])

    def contributions(self, X):
        """Array (rows, input features, classes) of SHAP contributions to each class probability."""
        values = self._tree.shap_values(self.prep.transform(X), check_additivity=False)
        values = np.stack(values, axis=-1) if isinstance(values, list) else np.asarray(values)
        out = np.zeros((values.shape[0], len(self.features), values.shape[2]))
        for column, feature_index in enumerate(self._source_index):
            out[:, feature_index, :] += values[:, column, :]
        return out

    def explain_row(self, row, class_name="Fail"):
        """Contributions for one student (a one-row DataFrame), largest effect first."""
        k = self.classes.index(class_name)
        contribution = self.contributions(row)[0, :, k]
        items = [
            {"feature": f, "value": _plain(row.iloc[0][f]), "contribution": round(float(c), 4)}
            for f, c in zip(self.features, contribution)
        ]
        return sorted(items, key=lambda item: abs(item["contribution"]), reverse=True)


def _plain(value):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    return value.item() if hasattr(value, "item") else value
