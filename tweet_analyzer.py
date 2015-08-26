import tweepy
import string
import re
import credentials
import http
from http import client
import urllib
from urllib import parse
import json

# Exceptions classes
class InputError(Exception): pass
class TwitterConnectionError(Exception): pass

def main():
    """Starts a new search"""

    print('')
    print('\t\t\t********************')
    print('\t\t\t*  TWEET ANALYSIS  *')
    print('\t\t\t********************')
    print('')

    try:
        user = {'consumer_key': credentials.consumer_key,
                'consumer_secret': credentials.consumer_secret,
                'twitter_token': credentials.twitter_token,
                'twitter_token_secret': credentials.twitter_token_secret}
    except:
        user = {'consumer_key': '',
                'consumer_secret': '',
                'twitter_token': '',
                'twitter_token_secret': ''}
    api = twitter_connection_factory(user)

    print('')
    print('Please enter the search parameters:')
    print('(Check https://dev.twitter.com/rest/public/search for advanced search options)')
    keyword = input('\t>> Keywords: ')
    date_start = input('\t>> Start date (yyyy-mm-dd): ')
    if date_start != '':
        date_start = 'since:%s' % date_start
    lang = input('\t>> Language: ')

    try:
        searched_tweets = search_tweets(api, keyword, date_start, lang)
    except:
        print('Failed to perform search.')
        exit()
    else:
        if len(searched_tweets)>0:
            save_search(searched_tweets)
            print('')
            print('Analyse tweets (y/n)? (It may take a while...)')
            ans = input('\t>> ').lower()
            if ans == 'y' or ans == 'yes':
                tweets = []
                for tweet in searched_tweets:
                    tweets.append(clean_tweet(str(tweet.text), lang))
                analyze_tweets(tweets, lang)
            print('')
            print('Search completed.')

def twitter_connection_factory(user):
    """Opens the connection to the TwitterAPI"""

    try:
        if user['consumer_key'] == '' or user['consumer_secret'] == '' \
                or user['twitter_token'] == '' or user['twitter_token_secret'] == '':
            print('Please enter your Twitter credentials:')
            user['consumer_key'] = input('\t>> Consumer key: ')
            user['consumer_secret'] = input('\t>> Consumer secret: ')
            user['twitter_token'] = input('\t>> Twitter token: ')
            user['twitter_token_secret'] = input('\t>> Twitter token secret: ')
            if user['consumer_key'] == '' or user['consumer_secret'] == '' \
                or user['twitter_token'] == '' or user['twitter_token_secret'] == '':
                raise InputError
    except InputError:
            print("Credentials invalid.")
            exit()

    print('Connecting to Twitter with following credentials: ')
    print('\tConsumer Key: %s' % user['consumer_key'])
    print('\tConsumer Secret: %s' % user['consumer_secret'])
    print('\tTwitter Token: %s' % user['twitter_token'])
    print('\tTwitter Token Secret: %s' % user['twitter_token_secret'])

    try:
        auth = tweepy.OAuthHandler(user['consumer_key'], user['consumer_secret'])
        auth.set_access_token(user['twitter_token'], user['twitter_token_secret'])
        api = tweepy.API(auth)
        api.get_user('twitter')
    except TwitterConnectionError:
        print("Failed to connect with Twitter.")
        exit()
    else:
        print('Connected to Twitter.')
        with open('credentials.py', 'w') as file:
            file.write("consumer_key = '%s'\n" % user['consumer_key'], )
            file.write("consumer_secret = '%s'\n" % user['consumer_secret'])
            file.write("twitter_token = '%s'\n" % user['twitter_token'])
            file.write("twitter_token_secret = '%s'\n" % user['twitter_token_secret'])
        file.close()
        return api

def search_tweets(api, keyword, date_start, lang):
    """Creates a query and searches for Tweets"""

    query = '%s %s' % (keyword, date_start)

    print('')
    print('Query created: %s' % query)
    print('Searching tweets...')

    searched_tweets = []
    max_tweets = 20000
    last_id = -1
    while len(searched_tweets) < max_tweets:
        count = max_tweets - len(searched_tweets)
        try:
            new_tweets = api.search(q=query, lang=lang, count=count, max_id=str(last_id - 1))
            if not new_tweets:
                break
            searched_tweets.extend(new_tweets)
            last_id = new_tweets[-1].id
        except:
            break

    print('Tweets found: %d' % len(searched_tweets))
    for tweet in searched_tweets[0:4]:
        try:
            print('\tUSER: ' + str(tweet.author.screen_name)[0:20] +
                  '; TWEET: ' + str(tweet.text).replace('\n', ' ').replace('\r', ' ')[0:30] +
                  '...; DATE: ' + str(tweet.created_at))
        except:
            continue
    return searched_tweets

def save_search(searched_tweets):
    with open('tweets.txt', 'w') as file:
        for tweet in searched_tweets:
            try:
                file.write(""""%s" ; "%s" ; "%s" ; "%s" ; "%s" ; "%s" ;\n""" %
                           (tweet.id,
                            str(tweet.text).replace('\n', ' ').replace('\r', ' '),
                            str(tweet.author.screen_name),
                            str(tweet.created_at),
                            str(tweet.place),
                            tweet.retweet_count))
            except UnicodeEncodeError:
                continue
            except Exception as e:
                print('Error! Could not save search! ' + str(e))
                return False
        print("Search saved in 'tweets.txt'")
    file.close()
    return True

def clean_tweet(tweet, lang=''):
    # Remove punctuation
    excludu = ['#', '@']
    for punct in string.punctuation:
        if punct not in excludu:
            tweet = tweet.replace(punct, '')

    # Remove special characters
    s_chars = ['\u00E1', '\u00E9', '\u00ED', '\u00F3', '\u00FA', '\u00E0', '\u00E8', '\u00EC', '\u00F2',
               '\u00F9', '\u00E3', '\u00F5', '\u00E2', '\u00EA', '\u00EE', '\u00F4', '\u00FB', '\u00E7',
               '\u00C1', '\u00C9','\u00CD', '\u00D3', '\u00DA', '\u00C0', '\u00C8', '\u00CC', '\u00D2',
               '\u00D9', '\u00C3', '\u00D5', '\u00C2', '\u00CA', '\u00CE', '\u00D4', '\u00DB', '\u00C7']
    r_chars = ['a', 'e', 'i', 'o', 'u', 'a', 'e', 'i', 'o',
               'u', 'a', 'o', 'a', 'e', 'i', 'o', 'u', 'c',
               'a', 'e', 'i', 'o', 'u', 'a', 'e', 'i', 'o',
               'u', 'a', 'o', 'a', 'e', 'i', 'o', 'u', 'c']
    for i in range(0, len(s_chars)):
        tweet = tweet.replace(s_chars[i], r_chars[i])

    # Remove urls
    tweet = re.sub(r'http[a-zA-Z0-9_]*', '', tweet)
    # Remove @s
    tweet = re.sub(r'@[a-zA-Z0-9]*', '', tweet)
    # Remove numbers
    tweet = re.sub(r'[0-9]*', '', tweet)

    # Remove punctuation
    punctuations = ['.', ',', '...', '!', '$', '%', '&', '(', ')', '*', '+', '-', '/', ':', ';', '<', '=',
                    '>', '?', '@', '[', '\\', ']', '^', '_', '{', '|', '}', '~', '"', "'"]
    for punct in punctuations:
        tweet = tweet.replace(punct, '')

    # Separate in tokens
    tweet = tweet.split()

    # Lower case
    tweet = [w.lower() for w in tweet]

    # Remove stopwords
    stopwords = ''
    if lang == 'pt':
        stopwords = ['de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'com', 'nao', 'uma',
                     'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'dos', 'como', 'mas', 'ao', 'ele',
                     'das', 'seu', 'sua', 'ou', 'quando', 'muito', 'nos', 'ja', 'eu', 'tambem',
                     'so', 'pelo', 'pela', 'ate', 'isso', 'ela', 'entre', 'depois', 'sem', 'mesmo',
                     'aos', 'seus', 'quem', 'nas', 'me', 'esse', 'eles', 'voce', 'essa', 'num', 'nem',
                     'suas', 'meu', 'minha', 'numa', 'pelos', 'elas', 'qual', 'nos', 'lhe',
                     'deles', 'essas', 'esses', 'pelas', 'este', 'dele', 'tu', 'te', 'voces', 'vos',
                     'lhes', 'meus', 'minhas', 'teu', 'tua', 'teus', 'tuas', 'nosso', 'nossa', 'nossos',
                     'nossas', 'dela', 'delas', 'esta', 'estes', 'estas', 'aquele', 'aquela', 'aqueles',
                     'aquelas', 'isto', 'aquilo', 'estou', 'estamos', 'estao', 'estive', 'esteve',
                     'estivemos', 'estiveram', 'estava', 'estavamos', 'estavam', 'estivera', 'estiveramos',
                     'esteja', 'estejamos', 'estejam', 'estivesse', 'estivessemos', 'estivessem', 'estiver',
                     'estivermos', 'estiverem', 'hei', 'ha', 'havemos', 'hao', 'houve', 'houvemos',
                     'houveram', 'houvera', 'houveramos', 'haja', 'hajamos', 'hajam', 'houvesse',
                     'houvessemos', 'houvessem', 'houver', 'houvermos', 'houverem', 'houverei', 'houvera',
                     'houveremos', 'houverao', 'houveria', 'houveriamos', 'houveriam', 'sou', 'somos', 'sao',
                     'era', 'eramos', 'eram', 'fui', 'foi', 'fomos', 'foram', 'fora', 'foramos', 'seja',
                     'sejamos', 'sejam', 'fosse', 'fossemos', 'fossem', 'for', 'formos', 'forem', 'serei',
                     'sera', 'seremos', 'serao', 'seria', 'seriamos', 'seriam', 'tenho', 'tem', 'temos', 'tem',
                     'tinha', 'tinhamos', 'tinham', 'tive', 'teve', 'tivemos', 'tiveram', 'tivera', 'tiveramos',
                     'tenha', 'tenhamos', 'tenham', 'tivesse', 'tivessemos', 'tivessem', 'tiver', 'tivermos',
                     'tiverem', 'terei', 'tera', 'teremos', 'terao', 'teria', 'teriamos', 'teriam']
    elif lang == 'en':
        stopwords = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
                     'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
                     'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
                     'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be',
                     'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an',
                     'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for',
                     'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above',
                     'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again',
                     'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
                     'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
                     'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now']
    elif lang == 'fr':
        stopwords = ['au', 'aux', 'avec', 'ce', 'ces', 'dans', 'de', 'des', 'du', 'elle', 'en', 'et', 'eux', 'il',
                     'je', 'la', 'le', 'leur', 'lui', 'ma', 'mais', 'me', 'meme', 'mes', 'moi', 'mon', 'ne', 'nos',
                     'notre', 'nous', 'on', 'ou', 'par', 'pas', 'pour', 'qu', 'que', 'qui', 'sa', 'se', 'ses', 'son',
                     'sur', 'ta', 'te', 'tes', 'toi', 'ton', 'tu', 'un', 'une', 'vos', 'votre', 'vous', 'c', 'd', 'j',
                     'l', 'a', 'm', 'n', 's', 't', 'y', 'ete', 'etee', 'etees', 'etes', 'etant', 'etante', 'etants',
                     'etantes', 'suis', 'es', 'est', 'sommes', 'etes', 'sont', 'serai', 'seras', 'sera', 'serons',
                     'serez', 'seront', 'serais', 'serait', 'serions', 'seriez', 'seraient', 'etais', 'etait', 'etions',
                     'etiez', 'etaient', 'fus', 'fut', 'fumes', 'futes', 'furent', 'sois', 'soit', 'soyons', 'soyez',
                     'soient', 'fusse', 'fusses', 'fut', 'fussions', 'fussiez', 'fussent', 'ayant', 'ayante', 'ayantes',
                     'ayants', 'eu', 'eue', 'eues', 'eus', 'ai', 'as', 'avons', 'avez', 'ont', 'aurai', 'auras', 'aura',
                     'aurons', 'aurez', 'auront', 'aurais', 'aurait', 'aurions', 'auriez', 'auraient', 'avais',
                     'avait', 'avions', 'aviez', 'avaient', 'eut', 'eumes', 'eutes', 'eurent', 'aie', 'aies', 'ait',
                     'ayons', 'ayez', 'aient', 'eusse', 'eusses', 'eut', 'eussions', 'eussiez', 'eussent']
    for w in tweet:
        if w in stopwords:
            tweet.remove(w)
    for w in tweet:
        if len(w) == 1:
            tweet.remove(w)

    return ' '.join(tweet)

# TODO improve sentiment analysis
def analyze_tweets(tweets, lang):
    print('')
    print('Analyzing tweets...')

    hashes = []
    words = []
    for tweet in tweets:
        for w in tweet.split(' '):
            words.append(w)
            if w[0] == '#':
                hashes.append(w)
                words.remove(w)

    sentiment_scores = []
    conn = http.client.HTTPConnection('sentiment.vivekn.com')
    headers = {'Accept': '*/*', 'User-Agent': 'runscope/0.1', 'Content-Type': 'application/x-www-form-urlencoded'}
    for tweet in tweets:
        param = urllib.parse.urlencode({'txt' : tweet})
        conn.request("POST", "/api/text/", param, headers)
        response = conn.getresponse()
        data = response.read()
        obj = json.loads(data.decode())
        if obj['result']['sentiment'] == 'Negative':
            sentiment_scores.append(-1)
        elif obj['result']['sentiment'] == 'Positive':
            sentiment_scores.append(1)
        else:
            sentiment_scores.append(0)
    print('\tAverage sentiment: %.3f' % (sum(sentiment_scores)/float(len(sentiment_scores))))

    common_words = []
    for w in set(words):
        common_words.append([words.count(w), w])
    common_words.sort(reverse = True)
    if len(common_words) >= 4:
        print('\tMost common words:')
        print('\t\t1- '+str(common_words[0][1])+': '+str(common_words[0][0]))
        print('\t\t2- '+str(common_words[1][1])+': '+str(common_words[1][0]))
        print('\t\t3- '+str(common_words[2][1])+': '+str(common_words[2][0]))
        print('\t\t4- '+str(common_words[3][1])+': '+str(common_words[3][0]))
        print('\t\t5- '+str(common_words[4][1])+': '+str(common_words[4][0]))

    common_hashes = []
    for h in set(hashes):
        common_hashes.append([hashes.count(h), h])
    common_hashes.sort(reverse = True)
    if len(common_hashes) >= 4:
        print('\tMost common hashtags:')
        print('\t\t1- '+str(common_hashes[0][1])+': '+str(common_hashes[0][0]))
        print('\t\t2- '+str(common_hashes[1][1])+': '+str(common_hashes[1][0]))
        print('\t\t3- '+str(common_hashes[2][1])+': '+str(common_hashes[2][0]))
        print('\t\t4- '+str(common_hashes[3][1])+': '+str(common_hashes[3][0]))
        print('\t\t5- '+str(common_hashes[4][1])+': '+str(common_hashes[4][0]))

if __name__ == '__main__':
    main()
