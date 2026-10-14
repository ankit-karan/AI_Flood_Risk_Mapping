from src.data_generation import generate_synthetic_data
from src.data_preprocessing import clean_data, get_preprocessor, split_data
from src.feature_engineering import add_features


def _df():
    return clean_data(generate_synthetic_data(n=300, seed=2))


def test_missing_value_handling():
    import numpy as np
    df = _df()
    assert df.isna().sum().sum() > 0  # raw has injected NaNs preserved for imputers
    X_train, _, _, _ = split_data(df)
    pre = get_preprocessor()
    Xt = pre.fit_transform(X_train)
    arr = Xt.toarray() if hasattr(Xt, "toarray") else Xt
    assert not np.isnan(arr).any()


def test_preprocessing_split():
    df = _df()
    X_train, X_test, y_train, y_test = split_data(df)
    assert len(X_train) > len(X_test)
    assert set(y_test.unique()) <= {"LOW", "MEDIUM", "HIGH"}
