# Import dependencies
import numpy as np
import pandas as pd
import tweepy
import time
import json

import boto3
import botocore

from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.externals import joblib

from keras.models import load_model

# import the model from AWS
# BUCKET_NAME = 'mlsomm' # replace with your bucket name
# KEY = 'ML_Somm.h5' # replace with your object key

# s3 = boto3.resource('s3')

# try:
    # s3.Bucket(BUCKET_NAME).download_file(KEY, 'somm_model.h5')
# except botocore.exceptions.ClientError as e:
    # if e.response['Error']['Code'] == "404":
        # print("The object does not exist.")
    # else:
        # raise

# Twitter API Keys
consumer_key = "AoUHxKdOO6aein5z81cdCDZxs"
consumer_secret = "MSEMsxbmglFzBUQsQpNoaS98GCvwDG1xDRrB9hrrvJjD1mrwr4"
access_token = "922955241078841344-oPc8kbdukcySJbL13OroEOYlF8CB9ZE"
access_token_secret = "nAc5b4zmxJ7hf1vC0HjNTZdISWglfrzqbCVnfrwuIdmHU"

# Twitter Credentials
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth, parser=tweepy.parsers.JSONParser())




def get_mentions(last_id, wine_description):
    mentions = api.mentions_timeline(since_id = last_id, count=10, result_type="recent")
    last_id = mentions[0]['id']
    for mention in mentions:
        wine_description = mention['text']
        target_user = '@' + mention['user']['screen_name']
        print("Wine description: " +  wine_description)
        print("Requested by: " + target_user)
    
    return last_id, wine_description, target_user

def runModel(wine_description):
    vectorizer = joblib.load('vectorizer.pkl')
    label_encoder = joblib.load('label_encoder.pkl') 

    # load the model
    model = load_model("somm_model.h5")
    # model = load_model("ML_Somm.h5")

    # test the data
    test = [wine_description]
    test_vec = vectorizer.transform(test)
    encoded_test = model.predict_classes(test_vec)
    predict_label = label_encoder.inverse_transform(encoded_test)
    print(predict_label)
    
    wine_type = predict_label[0]
    
    return wine_type

def get_wine_variety_response (variety):
    #read the CSV file
    sommData = pd.read_csv('Data/no_dups_wine_data.csv')
    
    output_tweets = []
    
    #find all the wineries for a particular variety to add to the output tweet
    variety_prediction = variety
    var_list = sommData.loc[sommData['variety'] == variety_prediction]
    
    #get the highest rated wines
    sorted_df = var_list.sort_values(["points"], ascending=[False])
    #sorted_df['winery'].head()
    wineries = sorted_df[['winery','price']]
    wineries['winery'].unique()[0:3]
    
    #get the average price for all wines in the TOP 3 wineries
    selected_wineries = wineries[wineries['winery'].isin(wineries['winery'].unique()[0:3])]
    avg_price = selected_wineries['price'].mean()
    
    wines = ("The highest rated " + variety_prediction + "s are from these wineries: " + wineries['winery'].unique()[0] + ", " \
        + wineries['winery'].unique()[1] + ", or " + wineries['winery'].unique()[2] +". Avg Price: $%.2f" % avg_price)
    output_tweets.append(wines)
    
    #least expensive
    sorted_df = var_list.sort_values(["price"], ascending=[True])
    #sorted_df['winery'].head()
    wineries = sorted_df[['winery','price']]
    
    #get the average price for all wines in the BOTTOM 3 wineries
    selected_wineries = wineries[wineries['winery'].isin(wineries['winery'].unique()[0:3])]
    avg_price = selected_wineries['price'].mean()
    wines= ("The least expensive " + variety_prediction + "s are from these wineries: " + wineries['winery'].unique()[0] + ", " \
        + wineries['winery'].unique()[1] + ", or " + wineries['winery'].unique()[2] +". Avg Price: $%.2f" % avg_price)
    output_tweets.append(wines)
    
    return output_tweets

def tweetBack (out_tweets, target):
    count = 0 
    while count < len(out_tweets):
        for i in out_tweets:
            api.update_status(i + " " + target)
            count+= 1 

last_id = None
wine_description = None
count = 0
runner = True
while runner == True:
    try:
        print("before get mentions")
        last_id, wine_description, target_user = get_mentions(last_id, wine_description)
        print("after get mentions")
        wine = runModel(wine_description)
        print("after model")
        out = get_wine_variety_response(wine)
        print("pre-tweetback")
        tweetBack(out, target_user)
        print(out)
        count +=1
    except:
        time.sleep(1)
    #print(since_id_)