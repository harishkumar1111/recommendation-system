import pandas as pd
import numpy as np
import pickle
import constants



logistic = pickle.load(file = open(constants.LOGISTIC_REGRESSION_PATH, 'rb'))

vectorizer = pickle.load(file = open(constants.VECTORIZER_PATH, 'rb'))

recommendation_model = pickle.load(file = open(constants.RECOMMENDER_PATH, 'rb'))

mapping = pickle.load(file = open(constants.MAPPING_PATH, 'rb'))

df = pickle.load(file = open(constants.DF_PATH, 'rb'))


def doRecommendations(username):

    tfidf_vectorizer = vectorizer
    lr = logistic
    
    try:
        recommendations = pd.DataFrame(recommendation_model.loc[username]).reset_index()
    except KeyError:
        errorMessage = f'Hey Mate! we tried hard but couldn\'t find the user "{username}", so we couldn\'t recommend anything \n\
         for "{username}", you can try again by select any of the below username to find their recommendations.'
        print(type(errorMessage))
        return errorMessage, None
    
    recommendations.rename(columns = { recommendations.columns[1]: 'pred_rating' }, inplace = True)
    recommendations = recommendations.sort_values(by = 'pred_rating', ascending = False)[0 : 20]

    recommendations = pd.merge(recommendations, mapping, left_on = 'id', right_on = 'id', how = 'left')

    recommendations = pd.merge(recommendations, df[['id', 'clean_review']], left_on = 'id', right_on = 'id', how = 'left')
    test_data = tfidf_vectorizer.transform(recommendations['clean_review'].values.astype('U'))

    sentiment_pred = lr.predict(test_data)
    sentiment_pred = pd.DataFrame(sentiment_pred,  columns = ['sentiment_predicted'])

    recommendations = pd.concat([recommendations, sentiment_pred], axis = 1)

    groupby = recommendations.groupby('id')

    pred_count_df = pd.DataFrame(groupby['sentiment_predicted'].count()).reset_index()
    pred_count_df.columns = ['id', 'review_count']

    pred_sum_df = pd.DataFrame(groupby['sentiment_predicted'].sum()).reset_index()
    pred_sum_df.columns = ['id', 'pred_pos_review']

    new_recom = pd.merge(pred_count_df, pred_sum_df, left_on = 'id', right_on = 'id', how = 'left')

    new_recom['positive_sentiment_rate'] = round(new_recom.pred_pos_review.div(new_recom.review_count).replace(np.inf, 0) * 100, 2)
    new_recom = new_recom.sort_values(by = 'positive_sentiment_rate', ascending = False)

    new_recom = pd.merge(new_recom, mapping, left_on = 'id', right_on = 'id', how = 'left')

    products = new_recom.head(20)

    
    productNameList = products['name'].tolist()
    posSentimentRateList = products['positive_sentiment_rate'].tolist()

    return productNameList, posSentimentRateList