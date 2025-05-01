import pandas as pd
from sklearn.decomposition import PCA
import numpy as np
import matplotlib.pyplot as plt
from sklearn.impute import SimpleImputer


def load_data(file_path):
    """读取Excel文件"""
    return pd.read_excel(file_path)


def separate_features_labels(data):
    """分离特征和标签"""
    X = data.iloc[:, :-1]
    y = data.iloc[:, -1]
    return X, y


def perform_pca(X):
    """对特征数据进行PCA"""
    pca = PCA()
    pca.fit(X)
    return pca


def calculate_feature_weights(pca):
    """计算每个原始特征的综合权重"""
    loadings = pca.components_
    feature_weights = np.mean(np.abs(loadings), axis=0)
    return feature_weights


def create_weight_dataframe(feature_names, feature_weights):
    """创建DataFrame并按权重排序"""
    weight_df = pd.DataFrame({
        '特征名': feature_names,
        '特征权重值': feature_weights
    })
    return weight_df


def save_to_csv(weight_df, file_path):
    """保存到CSV文件"""
    weight_df.to_csv(file_path, index=False)
    print("特征名和权重值已保存到 {} 文件中。".format(file_path))


def plot_weight_distribution(weight_df):
    """绘制排序图"""
    plt.figure(figsize=(10, 6))
    plt.bar(weight_df['特征名'], weight_df['特征权重值'])
    plt.xlabel('特征名')
    plt.ylabel('特征权重值')
    plt.title('特征权重排序图')
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.show()


def impute_missing_values(X):
    """使用SimpleImputer填充缺失值"""
    imputer = SimpleImputer(strategy='constant', fill_value=0)
    X_imputed = imputer.fit_transform(X)
    return pd.DataFrame(X_imputed, columns=X.columns)


# 主程序
if __name__ == "__main__":
    file_path = 'results/apollo_aggregated.xlsx'
    data = load_data(file_path)
    X, _ = separate_features_labels(data)  # 忽略标签y

    # 填充缺失值
    X_imputed = impute_missing_values(X)

    pca = perform_pca(X_imputed)
    feature_weights = calculate_feature_weights(pca)
    feature_names = X_imputed.columns
    weight_df = create_weight_dataframe(feature_names, feature_weights)
    save_to_csv(weight_df, 'results/feature_weights.csv')
    plot_weight_distribution(weight_df)